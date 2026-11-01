//! 앱(파이썬)과의 연결: 현재 사용자만 열 수 있는 이름 있는 파이프, 한 줄 JSON 요청 → 한 줄 JSON 응답.
//! 원격 연결은 거부하고(PIPE_REJECT_REMOTE_CLIENTS) 네트워크 소켓은 쓰지 않는다.

use std::sync::OnceLock;

use windows_sys::Win32::Foundation::{CloseHandle, ERROR_PIPE_CONNECTED, GetLastError, HANDLE, HLOCAL,
                                     INVALID_HANDLE_VALUE, LocalFree};
use windows_sys::Win32::Security::Authorization::{ConvertSidToStringSidW,
                                                  ConvertStringSecurityDescriptorToSecurityDescriptorW, SDDL_REVISION_1};
use windows_sys::Win32::Security::{GetTokenInformation, PSECURITY_DESCRIPTOR, SECURITY_ATTRIBUTES, TOKEN_QUERY,
                                   TOKEN_USER, TokenUser};
use windows_sys::Win32::Storage::FileSystem::{FlushFileBuffers, PIPE_ACCESS_DUPLEX, ReadFile, WriteFile};
use windows_sys::Win32::System::Pipes::{ConnectNamedPipe, CreateNamedPipeW, DisconnectNamedPipe,
                                        PIPE_READMODE_BYTE, PIPE_REJECT_REMOTE_CLIENTS, PIPE_TYPE_BYTE, PIPE_WAIT};
use windows_sys::Win32::System::Threading::{GetCurrentProcess, OpenProcessToken};
use windows_sys::Win32::UI::WindowsAndMessaging::{GetForegroundWindow, PostMessageW, WM_CLOSE};

use crate::json::{self, Value};
use crate::util::{base64, now, wide};
use crate::{VERSION, WM_PAUSE, WM_SETTINGS, app, main_hwnd, refresh_recent};

const MAX_REQUEST: usize = 64 * 1024;

fn user_sid() -> String {
    static SID: OnceLock<String> = OnceLock::new();
    SID.get_or_init(|| unsafe {
        let mut token: HANDLE = std::ptr::null_mut();
        if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) == 0 {
            return String::new();
        }
        let mut buf = vec![0u8; 256];
        let mut len = 0u32;
        let ok = GetTokenInformation(token, TokenUser, buf.as_mut_ptr() as _, buf.len() as u32, &mut len);
        CloseHandle(token);
        if ok == 0 {
            return String::new();
        }
        let user = &*(buf.as_ptr() as *const TOKEN_USER);
        let mut text: *mut u16 = std::ptr::null_mut();
        if ConvertSidToStringSidW(user.User.Sid, &mut text) == 0 {
            return String::new();
        }
        let mut n = 0;
        while *text.add(n) != 0 {
            n += 1;
        }
        let sid = String::from_utf16_lossy(std::slice::from_raw_parts(text, n));
        LocalFree(text as HLOCAL);
        sid
    })
    .clone()
}

pub fn pipe_name() -> String {
    format!("\\\\.\\pipe\\HwpAutoDocFit.kagent.{}", user_sid())
}

pub fn start() {
    std::thread::Builder::new().name("kagent-pipe".into()).stack_size(256 * 1024).spawn(serve).ok();
}

fn serve() {
    let sid = user_sid();
    if sid.is_empty() {
        return;
    }
    // 이 사용자와 SYSTEM만 접근(기본 보안은 Everyone 읽기를 줄 수 있어 직접 지정한다).
    let sddl = wide(&format!("D:P(A;;GA;;;{sid})(A;;GA;;;SY)"));
    let mut sd: PSECURITY_DESCRIPTOR = std::ptr::null_mut();
    if unsafe { ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl.as_ptr(), SDDL_REVISION_1, &mut sd,
                                                                     std::ptr::null_mut()) } == 0 {
        return;
    }
    let sa = SECURITY_ATTRIBUTES {
        nLength: std::mem::size_of::<SECURITY_ATTRIBUTES>() as u32,
        lpSecurityDescriptor: sd,
        bInheritHandle: 0,
    };
    let name = wide(&pipe_name());
    loop {
        let h = unsafe {
            CreateNamedPipeW(name.as_ptr(), PIPE_ACCESS_DUPLEX,
                             PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 4, 65536,
                             65536, 0, &sa)
        };
        if h == INVALID_HANDLE_VALUE {
            std::thread::sleep(std::time::Duration::from_millis(500));
            continue;
        }
        let connected = unsafe { ConnectNamedPipe(h, std::ptr::null_mut()) } != 0
            || unsafe { GetLastError() } == ERROR_PIPE_CONNECTED;
        if connected {
            if let Some(request) = read_line(h) {
                let response = match json::parse(&request) {
                    Some(v) => handle(&v),
                    None => error("요청을 읽지 못했습니다."),
                };
                let mut out = json::to_string(&response).into_bytes();
                out.push(b'\n');
                write_all(h, &out);
                unsafe { FlushFileBuffers(h) };
            }
            unsafe { DisconnectNamedPipe(h) };
        }
        unsafe { CloseHandle(h) };
    }
    #[allow(unreachable_code)]
    unsafe {
        LocalFree(sd as HLOCAL);
    }
}

fn read_line(h: HANDLE) -> Option<String> {
    let mut data = Vec::new();
    let mut buf = [0u8; 4096];
    loop {
        let mut n = 0u32;
        if unsafe { ReadFile(h, buf.as_mut_ptr(), buf.len() as u32, &mut n, std::ptr::null_mut()) } == 0 || n == 0 {
            break;
        }
        data.extend_from_slice(&buf[..n as usize]);
        if data.contains(&b'\n') || data.len() > MAX_REQUEST {
            break;
        }
    }
    if data.len() > MAX_REQUEST {
        return None;
    }
    let end = data.iter().position(|&b| b == b'\n').unwrap_or(data.len());
    String::from_utf8(data[..end].to_vec()).ok()
}

fn write_all(h: HANDLE, mut data: &[u8]) {
    while !data.is_empty() {
        let mut n = 0u32;
        let chunk = data.len().min(1 << 20) as u32;
        if unsafe { WriteFile(h, data.as_ptr(), chunk, &mut n, std::ptr::null_mut()) } == 0 || n == 0 {
            return;
        }
        data = &data[n as usize..];
    }
}

fn error(message: &str) -> Value {
    Value::obj(vec![("ok", false.into()), ("message", message.into())])
}

fn ok(mut extra: Vec<(&str, Value)>) -> Value {
    extra.insert(0, ("ok", true.into()));
    Value::obj(extra)
}

fn id_of(v: &Value) -> Option<i64> {
    v.num("id").filter(|n| n.fract() == 0.0 && *n > 0.0).map(|n| n as i64)
}

pub fn handle(v: &Value) -> Value {
    let a = app();
    let hwnd = main_hwnd();
    match v.str("cmd").unwrap_or("") {
        "status" => {
            let s = a.store.lock().unwrap();
            let settings = a.settings.lock().unwrap();
            ok(vec![
                ("version", VERSION.into()),
                ("paused", settings.paused.into()),
                ("items", s.count().unwrap_or(0).into()),
                ("total_bytes", s.total_bytes().unwrap_or(0).into()),
                ("hotkey", settings.hotkey.as_str().into()),
                ("hotkey_ok", a.hotkey_ok.load(std::sync::atomic::Ordering::Relaxed).into()),
            ])
        }
        "list" => {
            let limit = v.num("limit").unwrap_or(50.0).clamp(1.0, 1000.0) as usize;
            let items = a.store.lock().unwrap().recent(limit, v.str("query"));
            match items {
                Ok(items) => ok(vec![("items", Value::Arr(items.iter().map(|i| i.to_json()).collect()))]),
                Err(e) => error(&e),
            }
        }
        "get" => {
            let Some(id) = id_of(v) else { return error("항목을 확인해 주세요.") };
            match a.store.lock().unwrap().payload(id) {
                Ok(Some((kind, data, extra))) => {
                    let body: Value = match kind.as_str() {
                        "image" => base64(&data).into(),
                        _ => String::from_utf8_lossy(&data).into_owned().into(),
                    };
                    let formats = crate::clip::unpack_formats(&extra).into_iter().map(|(n, _)| Value::Str(n)).collect();
                    ok(vec![("id", id.into()), ("kind", kind.into()), ("data", body), ("formats", Value::Arr(formats))])
                }
                Ok(None) => error("항목이 없습니다."),
                Err(e) => error(&e),
            }
        }
        "restore" => {
            let Some(id) = id_of(v) else { return error("항목을 확인해 주세요.") };
            // 클립보드 쓰기는 창 스레드에서 해야 한다(소유 창 필요).
            let paste = v.bool("paste").unwrap_or(false);
            let target = if paste { (unsafe { GetForegroundWindow() }) as isize } else { 0 };
            unsafe { PostMessageW(hwnd, crate::WM_RESTORE, id as usize, target) };
            ok(vec![])
        }
        "delete" => {
            let Some(id) = id_of(v) else { return error("항목을 확인해 주세요.") };
            let done = a.store.lock().unwrap().delete(id).unwrap_or(false);
            refresh_recent();
            ok(vec![("deleted", done.into())])
        }
        "pin" => {
            let Some(id) = id_of(v) else { return error("항목을 확인해 주세요.") };
            let done = a.store.lock().unwrap().pin(id, v.bool("pinned").unwrap_or(true)).unwrap_or(false);
            refresh_recent();
            ok(vec![("changed", done.into())])
        }
        "clear" => {
            let n = a.store.lock().unwrap().clear(v.bool("keep_pinned").unwrap_or(true)).unwrap_or(0);
            refresh_recent();
            ok(vec![("deleted", (n as i64).into())])
        }
        "pause" | "resume" => {
            unsafe { PostMessageW(hwnd, WM_PAUSE, (v.str("cmd") == Some("pause")) as usize, 0) };
            ok(vec![])
        }
        "settings_get" => ok(vec![("settings", a.settings.lock().unwrap().to_json())]),
        "settings_set" => {
            let Some(new) = v.get("settings") else { return error("설정을 확인해 주세요.") };
            let snapshot = {
                let mut s = a.settings.lock().unwrap();
                s.apply(new);
                s.clone()
            };
            crate::save_settings();
            let _ = a.store.lock().unwrap().enforce(&snapshot, now());
            refresh_recent();
            unsafe { PostMessageW(hwnd, WM_SETTINGS, 0, 0) };
            ok(vec![("settings", snapshot.to_json())])
        }
        "quit" => {
            unsafe { PostMessageW(hwnd, WM_CLOSE, 0, 0) };
            ok(vec![])
        }
        _ => error("지원하지 않는 명령입니다."),
    }
}
