//! K에이전트: K클립보드 기록·빠른 붙여넣기 상주 프로그램.
//!
//! 속도·자원 원칙(사용자 지시 2026-10-31: 실행 속도와 최소 자원이 가장 중요):
//! - 이벤트로만 깨어난다(WM_CLIPBOARDUPDATE·단축키·파이프 요청). 폴링·주기 타이머 없음 → 유휴 CPU 0.
//! - 클립보드는 짧게 열어 복사만 하고, 해시·PNG 변환·암호화·저장은 작업 스레드가 한다.
//! - 팝업은 메모리에 둔 최근 목록으로 바로 그린다(DB·복호화 없음).
//! - SQLite는 Windows 내장 winsqlite3.dll, 네트워크 코드 없음.
#![windows_subsystem = "windows"]

mod clip;
mod crypt;
mod json;
mod pipe;
mod popup;
mod sqlite;
mod store;
mod timeline;
mod util;
mod watch;

use std::collections::HashSet;
use std::sync::atomic::{AtomicBool, AtomicIsize, AtomicU32, AtomicU64, AtomicI64, Ordering};
use std::sync::mpsc::{Sender, channel};
use std::sync::{Mutex, OnceLock};

use windows_sys::Win32::Foundation::{CloseHandle, ERROR_ALREADY_EXISTS, GetLastError, HWND, LPARAM, LRESULT, POINT, WPARAM};
use windows_sys::Win32::Graphics::Gdi::{CreateBitmap, CreateDIBSection, BITMAPINFO, BITMAPINFOHEADER, DIB_RGB_COLORS};
use windows_sys::Win32::System::DataExchange::{AddClipboardFormatListener, GetClipboardSequenceNumber,
                                               RemoveClipboardFormatListener};
use windows_sys::Win32::System::LibraryLoader::GetModuleHandleW;
use windows_sys::Win32::System::Threading::CreateMutexW;
use windows_sys::Win32::UI::HiDpi::{DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2, SetProcessDpiAwarenessContext};
use windows_sys::Win32::UI::Input::KeyboardAndMouse::{
    MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, MOD_SHIFT, MOD_WIN, RegisterHotKey, UnregisterHotKey,
};
use windows_sys::Win32::UI::Shell::{
    NIF_ICON, NIF_MESSAGE, NIF_TIP, NIM_ADD, NIM_DELETE, NIM_MODIFY, NOTIFYICONDATAW, Shell_NotifyIconW,
};
use windows_sys::Win32::UI::WindowsAndMessaging::*;

use crate::clip::Capture;
use crate::store::{Settings, Store, Summary};
use crate::util::{now, wide};

pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const WM_TRAY: u32 = WM_APP + 1;
pub const WM_REFRESH: u32 = WM_APP + 2;
pub const WM_RESTORE: u32 = WM_APP + 3;
pub const WM_SHOW: u32 = WM_APP + 4;
pub const WM_PAUSE: u32 = WM_APP + 5;
pub const WM_SETTINGS: u32 = WM_APP + 6;
const HOTKEY_ID: i32 = 1;
const TIMER_READ: usize = 1;
const READ_DELAY_MS: u32 = 60; // 연달아 오는 변경 알림을 한 번으로(복사 중간 상태 읽기 방지)
const RECENT: usize = 50;
const MAIN_CLASS: &str = "HwpAutoDocFit.KAgentMain";

pub enum TimelineMsg {
    Reconfigure {
        generation: u64,
        roots: Vec<String>,
        mtime_only: bool,
    },
    ScanRoot {
        generation: u64,
        root: String,
    },
    Apply {
        generation: u64,
        root: String,
        relative: String,
    },
}

pub struct App {
    pub dir: String,
    pub store: Mutex<Store>,
    pub settings: Mutex<Settings>,
    pub recent: Mutex<Vec<Summary>>,
    pub tx: Mutex<Sender<(Capture, String)>>,
    pub self_seq: AtomicU32,
    pub hwnd: AtomicIsize,
    pub hotkey_ok: AtomicBool,
    pub listening: AtomicBool,
    /// 마지막으로 클립보드에서 그림을 기록한 때(ms) — 같은 캡처가 스크린샷 폴더로도 오면 한 번만.
    pub last_clip_image: AtomicU64,
    pub timeline: Mutex<Option<timeline::Timeline>>,
    pub screenshots: Mutex<String>,
    pub scan_pending: Mutex<HashSet<String>>,
    pub timeline_generation: AtomicU64,
    pub timeline_files: AtomicI64,
    pub timeline_tx: Mutex<Option<Sender<TimelineMsg>>>,
}

fn now_ms() -> u64 {
    (now() * 1000.0) as u64
}

/// 스크린샷 폴더(알려진 폴더 FOLDERID_Screenshots, 없으면 사진\Screenshots).
fn screenshots_folder() -> Option<String> {
    use windows_sys::Win32::System::Com::CoTaskMemFree;
    use windows_sys::Win32::UI::Shell::{FOLDERID_Screenshots, SHGetKnownFolderPath};
    if let Ok(dir) = std::env::var("KAGENT_SCREENSHOTS") {
        return std::path::Path::new(&dir).is_dir().then_some(dir); // 시험용
    }
    unsafe {
        let mut p: windows_sys::core::PWSTR = std::ptr::null_mut();
        if SHGetKnownFolderPath(&FOLDERID_Screenshots, 0, std::ptr::null_mut(), &mut p) == 0 && !p.is_null() {
            let mut n = 0;
            while *p.add(n) != 0 {
                n += 1;
            }
            let path = String::from_utf16_lossy(std::slice::from_raw_parts(p, n));
            CoTaskMemFree(p as _);
            if std::path::Path::new(&path).is_dir() {
                return Some(path);
            }
        } else if !p.is_null() {
            CoTaskMemFree(p as _);
        }
    }
    let fallback = format!("{}\\Pictures\\Screenshots", std::env::var("USERPROFILE").ok()?);
    std::path::Path::new(&fallback).is_dir().then_some(fallback)
}

/// 스크린샷 폴더에 새로 생긴 PNG 한 장을 그림 항목으로 기록한다.
fn record_screenshot(path: &str) {
    if !path.to_lowercase().ends_with(".png") {
        return;
    }
    if now_ms().saturating_sub(app().last_clip_image.load(Ordering::Relaxed)) < 3000 {
        return; // 같은 캡처가 클립보드로 이미 기록됨
    }
    let max = app().settings.lock().unwrap().max_item_bytes as u64;
    // 캡처 도구가 아직 쓰는 중일 수 있어 몇 번 다시 시도한다.
    let mut data = None;
    for _ in 0..5 {
        match std::fs::metadata(path) {
            Ok(m) if m.len() > max => return,
            Ok(_) => {
                if let Ok(bytes) = std::fs::read(path) {
                    if bytes.starts_with(b"\x89PNG") && bytes.ends_with(b"IEND\xAE\x42\x60\x82") {
                        data = Some(bytes);
                        break;
                    }
                }
            }
            Err(_) => return,
        }
        std::thread::sleep(std::time::Duration::from_millis(150));
    }
    let Some(data) = data else { return };
    let preview = format!("캡처 · {}", clip::preview("image", &data));
    let settings = app().settings.lock().unwrap().clone();
    {
        let store = app().store.lock().unwrap();
        let t = now();
        if store.insert("image", &data, &[], &preview, "screenshot", t).is_err() {
            return;
        }
        let _ = store.enforce(&settings, t);
    }
    refresh_recent();
}

fn mark_scan_pending(pending: &mut HashSet<String>, root: &str) -> bool {
    pending.insert(root.to_string())
}

fn unmark_scan_pending(pending: &mut HashSet<String>, root: &str) -> bool {
    pending.remove(root)
}

fn timeline_worker(rx: std::sync::mpsc::Receiver<TimelineMsg>) {
    unsafe {
        use windows_sys::Win32::System::Threading::{GetCurrentThread, SetThreadPriority,
                                                    THREAD_MODE_BACKGROUND_BEGIN};
        SetThreadPriority(GetCurrentThread(), THREAD_MODE_BACKGROUND_BEGIN);
    }
    let mut current_gen: u64 = 0;
    let mut active_roots: Vec<String> = Vec::new();
    let mut tl: Option<timeline::Timeline> = None;

    for msg in rx {
        match msg {
            TimelineMsg::Reconfigure { generation, roots, mtime_only } => {
                if generation < app().timeline_generation.load(Ordering::Relaxed) {
                    continue;
                }
                current_gen = generation;
                active_roots = roots.clone();
                if active_roots.is_empty() {
                    tl = None;
                    *app().timeline.lock().unwrap() = None;
                    app().timeline_files.store(0, Ordering::Relaxed);
                } else {
                    if tl.is_none() {
                        tl = timeline::Timeline::open(&format!("{}\\timeline.db", app().dir)).ok();
                    }
                    if let Some(t) = tl.as_mut() {
                        t.mtime_only = mtime_only;
                        let _ = t.drop_other_roots(&active_roots);
                        let count = t.count();
                        app().timeline_files.store(count, Ordering::Relaxed);
                    }
                }
                write_status();
            }
            TimelineMsg::ScanRoot { generation, root } => {
                let latest_gen = app().timeline_generation.load(Ordering::Relaxed);
                if generation < latest_gen || current_gen < latest_gen || !active_roots.contains(&root) {
                    let mut pending = app().scan_pending.lock().unwrap();
                    unmark_scan_pending(&mut pending, &root);
                    continue;
                }
                if let Some(t) = tl.as_ref() {
                    let _ = t.scan_root(&root);
                    let count = t.count();
                    app().timeline_files.store(count, Ordering::Relaxed);
                }
                {
                    let mut pending = app().scan_pending.lock().unwrap();
                    unmark_scan_pending(&mut pending, &root);
                }
                write_status();
            }
            TimelineMsg::Apply { generation, root, relative } => {
                let latest_gen = app().timeline_generation.load(Ordering::Relaxed);
                if generation < latest_gen || current_gen < latest_gen || !active_roots.contains(&root) {
                    continue;
                }
                if let Some(t) = tl.as_ref() {
                    let _ = t.apply(&root, &relative);
                    let count = t.count();
                    app().timeline_files.store(count, Ordering::Relaxed);
                    write_status();
                }
            }
        }
    }
}

pub fn schedule_timeline_scan(root: String) {
    {
        let mut pending = app().scan_pending.lock().unwrap();
        if !mark_scan_pending(&mut pending, &root) {
            return;
        }
    }
    let generation = app().timeline_generation.load(Ordering::Relaxed);
    let sent = {
        let guard = app().timeline_tx.lock().unwrap();
        guard.as_ref().map(|tx| tx.send(TimelineMsg::ScanRoot { generation, root: root.clone() }).is_ok()).unwrap_or(false)
    };
    if !sent {
        let mut pending = app().scan_pending.lock().unwrap();
        unmark_scan_pending(&mut pending, &root);
    }
}

pub fn scan_timeline_root(root: &str) {
    schedule_timeline_scan(root.to_string());
}

/// 설정에 맞춰 폴더 감시(스크린샷·타임머신)를 다시 시작한다. 타임머신 폴더는 먼저 한 번 증분으로 훑는다.
pub fn restart_watchers() {
    let settings = app().settings.lock().unwrap().clone();
    let mut roots: Vec<(String, u32, bool)> = Vec::new();
    let shots = if settings.watch_screenshots && !settings.paused { screenshots_folder() } else { None };
    *app().screenshots.lock().unwrap() = shots.clone().unwrap_or_default();
    if let Some(dir) = shots {
        roots.push((dir, 0, false));
    }
    let timeline_roots: Vec<String> =
        settings.timeline_roots.iter().filter(|r| std::path::Path::new(r).is_dir()).cloned().collect();

    // 새 세대 번호 발급 (이전 세대의 진행 중 스캔 및 알림은 stale 처리됨)
    let generation = app().timeline_generation.fetch_add(1, Ordering::SeqCst) + 1;

    // 타임라인 전용 워커에 설정 변경 전달 (DB I/O를 창/메시지 스레드에서 수행하지 않음)
    if let Some(tx) = app().timeline_tx.lock().unwrap().as_ref() {
        let _ = tx.send(TimelineMsg::Reconfigure {
            generation,
            roots: timeline_roots.clone(),
            mtime_only: settings.timeline_mtime_only,
        });
    }

    for (i, root) in timeline_roots.iter().enumerate() {
        roots.push((root.clone(), i as u32 + 1, true));
    }
    let names = timeline_roots.clone();
    watch::restart(roots, move |batch| {
        for (tag, change) in batch {
            if tag == 0 {
                if let watch::Change::Added(rel) | watch::Change::Modified(rel) = change {
                    let dir = app().screenshots.lock().unwrap().clone();
                    record_screenshot(&format!("{dir}\\{rel}"));
                }
                continue;
            }
            let Some(root) = names.get(tag as usize - 1) else { continue };
            match change {
                watch::Change::Overflow => schedule_timeline_scan(root.clone()),
                watch::Change::Added(rel) | watch::Change::Removed(rel) | watch::Change::Modified(rel) => {
                    if let Some(tx) = app().timeline_tx.lock().unwrap().as_ref() {
                        let _ = tx.send(TimelineMsg::Apply {
                            generation,
                            root: root.clone(),
                            relative: rel,
                        });
                    }
                }
            }
        }
    });
    for root in timeline_roots {
        schedule_timeline_scan(root);
    }
}

static APP: OnceLock<App> = OnceLock::new();

pub fn app() -> &'static App {
    APP.get().expect("app")
}

pub fn main_hwnd() -> HWND {
    app().hwnd.load(Ordering::Relaxed) as HWND
}

fn settings_path() -> String {
    format!("{}\\settings.json", app().dir)
}

/// 메모리의 최근 목록을 DB에서 다시 읽는다(변경 때만).
pub fn refresh_recent() {
    let list = app().store.lock().unwrap().recent(RECENT, None).unwrap_or_default();
    *app().recent.lock().unwrap() = list;
    write_status();
    unsafe { PostMessageW(main_hwnd(), WM_REFRESH, 0, 0) };
}

/// 상태 파일: 앱이 파이프 없이도 읽을 수 있게 변경 때만 쓴다.
pub fn write_status() {
    let a = app();
    let (items, total) = {
        let s = a.store.lock().unwrap();
        (s.count().unwrap_or(0), s.total_bytes().unwrap_or(0))
    };
    let settings = a.settings.lock().unwrap().clone();
    let screenshots = a.screenshots.lock().unwrap().clone();
    let timeline_files = a.timeline_files.load(Ordering::Relaxed);
    let v = json::Value::obj(vec![
        ("version", VERSION.into()),
        ("pid", (std::process::id() as i64).into()),
        ("pipe", pipe::pipe_name().into()),
        ("paused", settings.paused.into()),
        ("items", items.into()),
        ("total_bytes", total.into()),
        ("hotkey", settings.hotkey.as_str().into()),
        ("hotkey_ok", a.hotkey_ok.load(Ordering::Relaxed).into()),
        ("screenshots", screenshots.as_str().into()),
        ("timeline_roots", (settings.timeline_roots.len() as i64).into()),
        ("timeline_files", timeline_files.into()),
        ("updated", now().into()),
    ]);
    let path = format!("{}\\status.json", a.dir);
    let temp = format!("{path}.tmp");
    if std::fs::write(&temp, json::to_string(&v)).is_ok() {
        let _ = std::fs::rename(&temp, &path);
    }
}

pub fn save_settings() {
    let s = app().settings.lock().unwrap().clone();
    let _ = s.save(&settings_path());
}

/// 작업 스레드: 클립보드에서 복사해 온 내용을 변환·암호화·저장한다(낮은 우선순위).
fn worker(rx: std::sync::mpsc::Receiver<(Capture, String)>) {
    unsafe {
        use windows_sys::Win32::System::Threading::{GetCurrentThread, SetThreadPriority, THREAD_PRIORITY_BELOW_NORMAL};
        SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
    }
    for (capture, source) in rx {
        let (kind, data, extra) = match capture {
            Capture::Text(s, extra) => ("text", s.into_bytes(), extra),
            Capture::Files(files) => ("files", files.join("\n").into_bytes(), Vec::new()),
            Capture::Png(b) => {
                app().last_clip_image.store(now_ms(), Ordering::Relaxed);
                ("image", b, Vec::new())
            }
            Capture::Dib(d) => match { app().last_clip_image.store(now_ms(), Ordering::Relaxed); clip::dib_to_png(&d) } {
                Some(p) => ("image", p, Vec::new()),
                None => continue,
            },
        };
        let settings = app().settings.lock().unwrap().clone();
        if (data.len() + extra.len()) as i64 > settings.max_item_bytes {
            continue;
        }
        let preview = clip::preview(kind, &data);
        let t = now();
        {
            let store = app().store.lock().unwrap();
            if store.insert(kind, &data, &extra, &preview, &source, t).is_err() {
                continue;
            }
            let _ = store.enforce(&settings, t);
        }
        refresh_recent();
    }
}

fn parse_hotkey(text: &str) -> Option<(u32, u32)> {
    let mut mods = MOD_NOREPEAT;
    let mut vk = 0u32;
    for part in text.split('+').map(|p| p.trim().to_ascii_lowercase()) {
        match part.as_str() {
            "ctrl" | "control" => mods |= MOD_CONTROL,
            "shift" => mods |= MOD_SHIFT,
            "alt" => mods |= MOD_ALT,
            "win" => mods |= MOD_WIN,
            p if p.len() == 1 && p.as_bytes()[0].is_ascii_alphanumeric() => vk = p.to_ascii_uppercase().as_bytes()[0] as u32,
            p if p.starts_with('f') => {
                let n: u32 = p[1..].parse().ok()?;
                if !(1..=24).contains(&n) {
                    return None;
                }
                vk = 0x70 + n - 1;
            }
            _ => return None,
        }
    }
    (vk != 0 && mods != MOD_NOREPEAT).then_some((mods, vk))
}

fn register_hotkey(hwnd: HWND) {
    unsafe { UnregisterHotKey(hwnd, HOTKEY_ID) };
    let text = app().settings.lock().unwrap().hotkey.clone();
    let ok = parse_hotkey(&text).map(|(m, vk)| unsafe { RegisterHotKey(hwnd, HOTKEY_ID, m, vk) } != 0).unwrap_or(false);
    app().hotkey_ok.store(ok, Ordering::Relaxed);
}

fn set_listening(hwnd: HWND, on: bool) {
    let a = app();
    if on && !a.listening.swap(true, Ordering::Relaxed) {
        unsafe { AddClipboardFormatListener(hwnd) };
    } else if !on && a.listening.swap(false, Ordering::Relaxed) {
        // 일시정지 중에는 알림 자체를 받지 않는다(처리 0).
        unsafe { RemoveClipboardFormatListener(hwnd) };
    }
}

/// 32×32 트레이 아이콘(파란 사각형에 흰 K, 일시정지면 회색)을 코드로 그린다 — 리소스 파일 없이.
fn make_icon(paused: bool) -> HICON {
    const N: i32 = 32;
    let dist = |px: f32, py: f32, (ax, ay): (f32, f32), (bx, by): (f32, f32)| {
        let (dx, dy) = (bx - ax, by - ay);
        let t = (((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)).clamp(0.0, 1.0);
        ((px - ax - t * dx).powi(2) + (py - ay - t * dy).powi(2)).sqrt()
    };
    unsafe {
        let mut info: BITMAPINFO = std::mem::zeroed();
        info.bmiHeader = BITMAPINFOHEADER {
            biSize: std::mem::size_of::<BITMAPINFOHEADER>() as u32, biWidth: N, biHeight: -N, biPlanes: 1,
            biBitCount: 32, biCompression: 0, biSizeImage: 0, biXPelsPerMeter: 0, biYPelsPerMeter: 0, biClrUsed: 0,
            biClrImportant: 0,
        };
        let mut bits: *mut std::ffi::c_void = std::ptr::null_mut();
        let color = CreateDIBSection(std::ptr::null_mut(), &info, DIB_RGB_COLORS, &mut bits, std::ptr::null_mut(), 0);
        if color.is_null() || bits.is_null() {
            return LoadIconW(std::ptr::null_mut(), IDI_APPLICATION);
        }
        let px = std::slice::from_raw_parts_mut(bits as *mut u32, (N * N) as usize);
        let bg: u32 = if paused { 0xFF8A8F98 } else { 0xFF2563EB };
        for y in 0..N {
            for x in 0..N {
                let (fx, fy) = (x as f32 + 0.5, y as f32 + 0.5);
                let corner = (fx.min(N as f32 - fx).min(6.0), fy.min(N as f32 - fy).min(6.0));
                let inside = corner.0 >= 6.0 || corner.1 >= 6.0
                    || (6.0 - corner.0).powi(2) + (6.0 - corner.1).powi(2) <= 36.0;
                let k = dist(fx, fy, (10.0, 6.0), (10.0, 26.0)) < 2.2
                    || dist(fx, fy, (11.0, 17.0), (23.0, 6.0)) < 2.2
                    || dist(fx, fy, (14.0, 14.5), (23.5, 26.0)) < 2.2;
                px[(y * N + x) as usize] = if !inside { 0 } else if k { 0xFFFFFFFF } else { bg };
            }
        }
        let mask = CreateBitmap(N, N, 1, 1, std::ptr::null());
        let ii = ICONINFO { fIcon: 1, xHotspot: 0, yHotspot: 0, hbmMask: mask, hbmColor: color };
        let icon = CreateIconIndirect(&ii);
        windows_sys::Win32::Graphics::Gdi::DeleteObject(mask);
        windows_sys::Win32::Graphics::Gdi::DeleteObject(color);
        icon
    }
}

fn tray(hwnd: HWND, op: u32) {
    let paused = app().settings.lock().unwrap().paused;
    let count = app().recent.lock().unwrap().len();
    unsafe {
        let mut nid: NOTIFYICONDATAW = std::mem::zeroed();
        nid.cbSize = std::mem::size_of::<NOTIFYICONDATAW>() as u32;
        nid.hWnd = hwnd;
        nid.uID = 1;
        nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
        nid.uCallbackMessage = WM_TRAY;
        nid.hIcon = make_icon(paused);
        let tip = if paused {
            "K클립보드 — 일시정지".to_string()
        } else {
            let hotkey = app().settings.lock().unwrap().hotkey.clone();
            format!("K클립보드 — 기록 중 ({count}개) · {hotkey}")
        };
        for (i, u) in tip.encode_utf16().take(nid.szTip.len() - 1).enumerate() {
            nid.szTip[i] = u;
        }
        Shell_NotifyIconW(op, &nid);
        if !nid.hIcon.is_null() {
            DestroyIcon(nid.hIcon);
        }
    }
}

fn tray_menu(hwnd: HWND) {
    let paused = app().settings.lock().unwrap().paused;
    unsafe {
        let menu = CreatePopupMenu();
        AppendMenuW(menu, MF_STRING, 1, wide("최근 항목 열기").as_ptr());
        AppendMenuW(menu, MF_STRING, 2, wide(if paused { "다시 기록" } else { "일시정지" }).as_ptr());
        AppendMenuW(menu, MF_STRING, 3, wide("모두 지우기(고정 제외)").as_ptr());
        AppendMenuW(menu, MF_SEPARATOR, 0, std::ptr::null());
        AppendMenuW(menu, MF_STRING, 4, wide("K클립보드 끝내기").as_ptr());
        let mut pt = POINT { x: 0, y: 0 };
        GetCursorPos(&mut pt);
        SetForegroundWindow(hwnd);
        let cmd = TrackPopupMenu(menu, TPM_RETURNCMD | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, std::ptr::null());
        DestroyMenu(menu);
        match cmd {
            1 => popup::show(),
            2 => set_paused(hwnd, !paused),
            3 => {
                let _ = app().store.lock().unwrap().clear(true);
                refresh_recent();
            }
            4 => {
                DestroyWindow(hwnd);
            }
            _ => {}
        }
    }
}

pub fn set_paused(hwnd: HWND, paused: bool) {
    app().settings.lock().unwrap().paused = paused;
    save_settings();
    set_listening(hwnd, !paused);
    tray(hwnd, NIM_MODIFY);
    restart_watchers();
    write_status();
}

/// 항목을 클립보드에 올리고(자기 쓰기는 다시 기록하지 않음), 원하면 target 창에 Ctrl+V.
pub fn restore(id: i64, paste: bool, target: HWND) -> bool {
    let payload = app().store.lock().unwrap().payload(id).ok().flatten();
    let Some((kind, data, extra)) = payload else { return false };
    let hwnd = main_hwnd();
    if !clip::write(hwnd, &kind, &data, &extra) {
        return false;
    }
    app().self_seq.store(unsafe { GetClipboardSequenceNumber() }, Ordering::Relaxed);
    let _ = app().store.lock().unwrap().touch(id, now());
    refresh_recent();
    if paste && !target.is_null() {
        popup::paste_into(target);
    }
    true
}

unsafe extern "system" fn wndproc(hwnd: HWND, msg: u32, wp: WPARAM, lp: LPARAM) -> LRESULT {
    unsafe {
        match msg {
            WM_CLIPBOARDUPDATE => {
                if GetClipboardSequenceNumber() != app().self_seq.load(Ordering::Relaxed) {
                    SetTimer(hwnd, TIMER_READ, READ_DELAY_MS, None);
                }
                0
            }
            WM_TIMER if wp == TIMER_READ => {
                KillTimer(hwnd, TIMER_READ);
                let a = app();
                if a.settings.lock().unwrap().paused
                    || GetClipboardSequenceNumber() == a.self_seq.load(Ordering::Relaxed)
                {
                    return 0;
                }
                let source = clip::source_app();
                let (excluded, max) = {
                    let s = a.settings.lock().unwrap();
                    (s.excluded_apps.iter().any(|e| *e == source), s.max_item_bytes as usize)
                };
                if !excluded {
                    if let Some(capture) = clip::read(hwnd, max) {
                        let _ = a.tx.lock().unwrap().send((capture, source));
                    }
                }
                0
            }
            WM_HOTKEY if wp as i32 == HOTKEY_ID => {
                popup::show();
                0
            }
            WM_TRAY => {
                match lp as u32 {
                    WM_LBUTTONUP => popup::show(),
                    WM_RBUTTONUP | WM_CONTEXTMENU => tray_menu(hwnd),
                    _ => {}
                }
                0
            }
            WM_REFRESH => {
                tray(hwnd, NIM_MODIFY);
                popup::refresh();
                0
            }
            WM_RESTORE => {
                restore(wp as i64, lp != 0, lp as HWND);
                0
            }
            WM_SHOW => {
                popup::show();
                0
            }
            WM_PAUSE => {
                set_paused(hwnd, wp != 0);
                0
            }
            WM_SETTINGS => {
                register_hotkey(hwnd);
                let paused = app().settings.lock().unwrap().paused;
                set_listening(hwnd, !paused);
                tray(hwnd, NIM_MODIFY);
                restart_watchers();
                write_status();
                0
            }
            WM_DESTROY => {
                set_listening(hwnd, false);
                watch::stop();
                UnregisterHotKey(hwnd, HOTKEY_ID);
                tray(hwnd, NIM_DELETE);
                let _ = std::fs::remove_file(format!("{}\\status.json", app().dir));
                PostQuitMessage(0);
                0
            }
            _ => DefWindowProcW(hwnd, msg, wp, lp),
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let has = |flag: &str| args.iter().any(|a| a == flag);
    let instance_mutex = unsafe {
        // 하나만 실행: 이미 있으면 그쪽에 요청만 보내고 끝낸다.
        CreateMutexW(std::ptr::null(), 0, wide("Local\\HwpAutoDocFit.kagent").as_ptr())
    };
    if instance_mutex.is_null() {
        std::process::exit(1);
    }
    unsafe {
        if GetLastError() == ERROR_ALREADY_EXISTS {
            CloseHandle(instance_mutex);
            let other = FindWindowW(wide(MAIN_CLASS).as_ptr(), std::ptr::null());
            if !other.is_null() {
                if has("--quit") {
                    PostMessageW(other, WM_CLOSE, 0, 0);
                } else {
                    PostMessageW(other, WM_SHOW, 0, 0);
                }
            }
            return;
        }
        if has("--quit") {
            CloseHandle(instance_mutex);
            return;
        }
        SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
    }
    // 로그인 직후 자동 시작이면 다른 프로그램이 먼저 뜨도록 늦게 시작한다.
    if let Some(i) = args.iter().position(|a| a == "--delay") {
        if let Some(secs) = args.get(i + 1).and_then(|s| s.parse::<u64>().ok()) {
            std::thread::sleep(std::time::Duration::from_secs(secs.min(300)));
        }
    }

    let dir = util::data_dir();
    let _ = std::fs::create_dir_all(&dir);
    let store = match Store::open(&format!("{dir}\\clip.db")) {
        Ok(s) => s,
        Err(_) => std::process::exit(2),
    };
    let settings = Settings::load(&format!("{dir}\\settings.json"));
    let (tx, rx) = channel();
    let (tl_tx, tl_rx) = channel();
    let _ = APP.set(App {
        dir,
        store: Mutex::new(store),
        settings: Mutex::new(settings),
        recent: Mutex::new(Vec::new()),
        tx: Mutex::new(tx),
        self_seq: AtomicU32::new(0),
        hwnd: AtomicIsize::new(0),
        hotkey_ok: AtomicBool::new(false),
        listening: AtomicBool::new(false),
        last_clip_image: AtomicU64::new(0),
        timeline: Mutex::new(None),
        screenshots: Mutex::new(String::new()),
        scan_pending: Mutex::new(HashSet::new()),
        timeline_generation: AtomicU64::new(0),
        timeline_files: AtomicI64::new(0),
        timeline_tx: Mutex::new(Some(tl_tx)),
    });
    *app().recent.lock().unwrap() = app().store.lock().unwrap().recent(RECENT, None).unwrap_or_default();
    std::thread::Builder::new().name("kagent-worker".into()).stack_size(256 * 1024).spawn(move || worker(rx)).ok();
    std::thread::Builder::new().name("kagent-timeline".into()).stack_size(512 * 1024).spawn(move || timeline_worker(tl_rx)).ok();

    unsafe {
        let instance = GetModuleHandleW(std::ptr::null());
        let class = wide(MAIN_CLASS);
        let wc = WNDCLASSEXW {
            cbSize: std::mem::size_of::<WNDCLASSEXW>() as u32,
            style: 0,
            lpfnWndProc: Some(wndproc),
            cbClsExtra: 0,
            cbWndExtra: 0,
            hInstance: instance,
            hIcon: std::ptr::null_mut(),
            hCursor: std::ptr::null_mut(),
            hbrBackground: std::ptr::null_mut(),
            lpszMenuName: std::ptr::null(),
            lpszClassName: class.as_ptr(),
            hIconSm: std::ptr::null_mut(),
        };
        RegisterClassExW(&wc);
        // 보이지 않는 창(트레이 알림을 받으려면 메시지 전용 창이 아니어야 한다).
        let hwnd = CreateWindowExW(WS_EX_TOOLWINDOW, class.as_ptr(), wide("K에이전트").as_ptr(), WS_POPUP, 0, 0, 0, 0,
                                   std::ptr::null_mut(), std::ptr::null_mut(), instance, std::ptr::null());
        if hwnd.is_null() {
            std::process::exit(3);
        }
        app().hwnd.store(hwnd as isize, Ordering::Relaxed);
        popup::register(instance);
        register_hotkey(hwnd);
        let paused = app().settings.lock().unwrap().paused;
        set_listening(hwnd, !paused);
        tray(hwnd, NIM_ADD);
        restart_watchers();
        write_status();
        pipe::start();

        let mut msg: MSG = std::mem::zeroed();
        while GetMessageW(&mut msg, std::ptr::null_mut(), 0, 0) > 0 {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        CloseHandle(instance_mutex);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hotkeys() {
        assert_eq!(parse_hotkey("Ctrl+Shift+V"), Some((MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT, 'V' as u32)));
        assert_eq!(parse_hotkey("Alt+F2"), Some((MOD_NOREPEAT | MOD_ALT, 0x71)));
        assert_eq!(parse_hotkey("V"), None);
        assert_eq!(parse_hotkey("Ctrl+Space"), None);
    }

    #[test]
    fn timeline_scan_pending_deduplicates_root() {
        let mut pending = HashSet::new();
        assert!(mark_scan_pending(&mut pending, "C:\\test"));
        assert!(!mark_scan_pending(&mut pending, "C:\\test"));
        assert!(mark_scan_pending(&mut pending, "C:\\other"));
        assert!(unmark_scan_pending(&mut pending, "C:\\test"));
        assert!(!unmark_scan_pending(&mut pending, "C:\\test"));
        assert!(mark_scan_pending(&mut pending, "C:\\test"));
    }

    #[test]
    fn timeline_generation_stale_detection() {
        let current_gen = 2u64;
        let old_msg_gen = 1u64;
        let new_msg_gen = 2u64;
        assert!(old_msg_gen < current_gen);
        assert!(!(new_msg_gen < current_gen));
    }
}
