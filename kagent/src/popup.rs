//! 빠른 붙여넣기 팝업: 단축키를 누르면 마우스 옆에 최근 항목을 바로 그린다(메모리 목록, DB 읽기 없음).
//! 숫자 1~9·↑↓·Enter로 고르면 원래 창으로 돌아가 붙여넣는다. Esc·바깥 클릭은 닫기.
//! 글자를 치면 바로 찾는다(한글 입력 중인 글자도 반영). 찾는 중에는 숫자도 찾을 글자로 쓴다.

use std::sync::Mutex;
use std::sync::atomic::{AtomicIsize, Ordering};

use windows_sys::Win32::Foundation::{HINSTANCE, HWND, LPARAM, LRESULT, POINT, RECT, WPARAM};
use windows_sys::Win32::Graphics::Gdi::*;
use windows_sys::Win32::UI::HiDpi::GetDpiForWindow;
use windows_sys::Win32::UI::Input::Ime::{GCS_COMPSTR, ImmGetCompositionStringW, ImmGetContext, ImmReleaseContext};
use windows_sys::Win32::UI::Input::KeyboardAndMouse::{
    GetAsyncKeyState, SetFocus, INPUT, INPUT_0, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP, SendInput, VIRTUAL_KEY, VK_CONTROL,
    VK_DELETE, VK_DOWN, VK_END, VK_ESCAPE, VK_HOME, VK_LMENU, VK_LWIN, VK_MENU, VK_NEXT, VK_PRIOR, VK_RETURN,
    VK_BACK, VK_RMENU, VK_RWIN, VK_SHIFT, VK_UP,
};
use windows_sys::Win32::UI::WindowsAndMessaging::*;

use crate::store::Summary;
use crate::open_item;
use crate::util::wide;
use crate::{app, main_hwnd, refresh_recent, restore};

const CLASS: &str = "HwpAutoDocFit.KAgentPopup";
const VISIBLE: usize = 12;
const BASE_W: i32 = 440;
const ROW_H: i32 = 30;
const HEAD_H: i32 = 30;
/// 접힌 창 높이. 두꺼운 틀 안쪽에 머리글이 다 보이도록 틀 높이를 더한다.
const COLLAPSED_H: i32 = HEAD_H + 12;
/// 머리글 오른쪽 '항상 위' 단추의 폭.
const PIN_W: i32 = 76;
/// 머리글 맨 오른쪽 닫기(X) 단추의 폭.
const CLOSE_W: i32 = 30;
const CAPTURE_W: i32 = 54;
const CLEAR_W: i32 = 54;
const COLLAPSE_W: i32 = 34;
const ROW_PIN_W: i32 = 28;
const ROW_DELETE_W: i32 = 28;
const MIN_W: i32 = 300;
const MIN_H: i32 = 90;

struct State {
    items: Vec<Summary>,
    sel: usize,
    top: usize,
    target: isize,
    hover: Option<usize>,
    /// 확정된 찾기 글자와 한글 입력 중인 글자.
    query: String,
    comp: String,
    seq: u64,
}

static STATE: Mutex<State> = Mutex::new(State {
    items: Vec::new(), sel: 0, top: 0, target: 0, hover: None, query: String::new(), comp: String::new(), seq: 0,
});

impl State {
    fn needle(&self) -> String {
        format!("{}{}", self.query, self.comp)
    }
}

/// 찾기 글자로 목록을 다시 만든다. 빈 찾기는 메모리 목록, 찾기는 저장소(복호화 결과 캐시)에서.
/// 단계별로 잠금을 해제하여 STATE와 DB/recent 동시 잠금이 없도록 하고,
/// sequence 번호 검증을 통해 이전 검색 결과가 새 입력을 덮어쓰지 않도록 보장한다.
fn refilter() {
    let (needle, cur_seq) = {
        let mut st = STATE.lock().unwrap();
        st.seq += 1;
        (st.needle(), st.seq)
    };
        let items = if needle.trim().is_empty() {
        app().recent.lock().unwrap().clone()
    } else {
        app().store.lock().unwrap().recent(50, Some(needle.trim())).unwrap_or_default()
    };
    let mut st = STATE.lock().unwrap();
    if st.seq != cur_seq || st.needle() != needle {
        return;
    }
    st.items = items;
    st.sel = 0;
    st.top = 0;
    st.hover = None;
    drop(st);
    unsafe { InvalidateRect(popup_hwnd(), std::ptr::null(), 0) };
}
static HWND_POPUP: AtomicIsize = AtomicIsize::new(0);

fn popup_hwnd() -> HWND {
    HWND_POPUP.load(Ordering::Relaxed) as HWND
}

pub fn register(instance: HINSTANCE) {
    unsafe {
        let class = wide(CLASS);
        let wc = WNDCLASSEXW {
            cbSize: std::mem::size_of::<WNDCLASSEXW>() as u32,
            style: CS_DROPSHADOW,
            lpfnWndProc: Some(wndproc),
            cbClsExtra: 0,
            cbWndExtra: 0,
            hInstance: instance,
            hIcon: std::ptr::null_mut(),
            hCursor: LoadCursorW(std::ptr::null_mut(), IDC_ARROW),
            hbrBackground: std::ptr::null_mut(),
            lpszMenuName: std::ptr::null(),
            lpszClassName: class.as_ptr(),
            hIconSm: std::ptr::null_mut(),
        };
        RegisterClassExW(&wc);
        let topmost = app().settings.lock().unwrap().always_on_top;
        let ex_style = WS_EX_TOOLWINDOW | if topmost { WS_EX_TOPMOST } else { 0 };
        let hwnd = CreateWindowExW(ex_style, class.as_ptr(), wide("몽땅클립보드").as_ptr(),
                                   WS_POPUP | WS_BORDER | WS_THICKFRAME, 0, 0, BASE_W, 200, std::ptr::null_mut(),
                                   std::ptr::null_mut(), instance, std::ptr::null());
        HWND_POPUP.store(hwnd as isize, Ordering::Relaxed);
    }
}

fn scale(hwnd: HWND, v: i32) -> i32 {
    let dpi = unsafe { GetDpiForWindow(hwnd) }.max(96) as i32;
    v * dpi / 96
}

/// 단축키·트레이에서 부른다. 지금 앞 창을 기억해 두고 마우스 옆에 띄운다.
pub fn show() {
    let hwnd = popup_hwnd();
    if hwnd.is_null() {
        return;
    }
    let recent_items = app().recent.lock().unwrap().clone();
    unsafe {
        let settings = app().settings.lock().unwrap().clone();
        if settings.sticky_popup && IsWindowVisible(hwnd) != 0 {
            ShowWindow(hwnd, SW_HIDE);
            return;
        }
        let fg = GetForegroundWindow();
        let mut st = STATE.lock().unwrap();
        st.seq += 1;
        if fg != hwnd && fg != main_hwnd() {
            st.target = fg as isize;
        }
        st.items = recent_items;
        st.sel = 0;
        st.top = 0;
        st.hover = None;
        st.query.clear();
        st.comp.clear();
        // 찾기 결과가 늘 수 있으므로 항목이 적어도 창은 몇 줄 여유를 둔다.
        let rows = st.items.len().clamp(5, VISIBLE) as i32;
        drop(st);
        let mut pt = POINT { x: 0, y: 0 };
        GetCursorPos(&mut pt);
        // 창을 그 모니터의 DPI로 먼저 옮긴 뒤 크기를 정한다.
        SetWindowPos(hwnd, std::ptr::null_mut(), pt.x, pt.y, 1, 1, SWP_NOZORDER | SWP_NOACTIVATE);
        let (default_w, default_h) = (scale(hwnd, BASE_W), scale(hwnd, HEAD_H + ROW_H * rows + 8));
        let monitor = MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
        let mut mi: MONITORINFO = std::mem::zeroed();
        mi.cbSize = std::mem::size_of::<MONITORINFO>() as u32;
        GetMonitorInfoW(monitor, &mut mi);
        let wa = mi.rcWork;
        let (sticker, collapsed, saved_x, saved_y, saved_w, saved_h) = {
            let s = app().settings.lock().unwrap();
            (s.sticky_popup, s.popup_collapsed, s.popup_x, s.popup_y, s.popup_width, s.popup_height)
        };
        let dpi = GetDpiForWindow(hwnd).max(96) as i64;
        let saved_x_px = saved_x * dpi / 96;
        let saved_y_px = saved_y * dpi / 96;
        let saved_w_px = saved_w * dpi / 96;
        let saved_h_px = saved_h * dpi / 96;
        let saved_rect_valid = sticker && saved_x_px >= wa.left as i64 && saved_y_px >= wa.top as i64
            && saved_w > 0 && saved_h > 0
            && saved_x_px + saved_w_px <= wa.right as i64 && saved_y_px + saved_h_px <= wa.bottom as i64;
        let (x, y, w, mut h) = if saved_rect_valid {
            (saved_x_px as i32, saved_y_px as i32, saved_w_px as i32, saved_h_px as i32)
        } else {
            ((pt.x + 8).min(wa.right - default_w).max(wa.left),
             (pt.y + 8).min(wa.bottom - default_h).max(wa.top), default_w, default_h)
        };
        if collapsed { h = scale(hwnd, COLLAPSED_H); }
        SetWindowPos(hwnd, if settings.always_on_top { HWND_TOPMOST } else { HWND_NOTOPMOST },
                     x, y, w, h, SWP_SHOWWINDOW);
        SetForegroundWindow(hwnd);
        SetFocus(hwnd);
        InvalidateRect(hwnd, std::ptr::null(), 0);
    }
}

/// 설정 화면에서 항상 위 상태를 바꾸면 열린 창에도 즉시 반영한다.
pub fn apply_settings() {
    let hwnd = popup_hwnd();
    if hwnd.is_null() { return; }
    let topmost = app().settings.lock().unwrap().always_on_top;
    unsafe {
        SetWindowPos(hwnd, if topmost { HWND_TOPMOST } else { HWND_NOTOPMOST }, 0, 0, 0, 0,
                     SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        InvalidateRect(hwnd, std::ptr::null(), 0);
    }
}

/// 목록이 바뀌면(보이는 동안) 다시 그린다.
pub fn refresh() {
    let hwnd = popup_hwnd();
    if hwnd.is_null() || unsafe { IsWindowVisible(hwnd) } == 0 {
        return;
    }
    let (searching, cur_seq) = {
        let st = STATE.lock().unwrap();
        (!st.needle().is_empty(), st.seq)
    };
    if searching {
        refilter();
        return;
    }
    let recent_items = app().recent.lock().unwrap().clone();
    let mut st = STATE.lock().unwrap();
    if st.seq != cur_seq || !st.needle().is_empty() {
        return;
    }
    st.items = recent_items;
    st.sel = st.sel.min(st.items.len().saturating_sub(1));
    drop(st);
    unsafe { InvalidateRect(hwnd, std::ptr::null(), 0) };
}

fn hide() {
    unsafe { ShowWindow(popup_hwnd(), SW_HIDE) };
}

fn key(vk: VIRTUAL_KEY, up: bool) -> INPUT {
    INPUT {
        r#type: INPUT_KEYBOARD,
        Anonymous: INPUT_0 {
            ki: KEYBDINPUT { wVk: vk, wScan: 0, dwFlags: if up { KEYEVENTF_KEYUP } else { 0 }, time: 0, dwExtraInfo: 0 },
        },
    }
}

/// target 창을 앞으로 가져와 Ctrl+V를 보낸다. 아직 눌린 Shift·Alt·Win은 먼저 뗀다.
pub fn paste_into(target: HWND) {
    unsafe {
        SetForegroundWindow(target);
        let mut inputs = Vec::new();
        for vk in [VK_SHIFT, VK_MENU, VK_LMENU, VK_RMENU, VK_LWIN, VK_RWIN] {
            if GetAsyncKeyState(vk as i32) as u16 & 0x8000 != 0 {
                inputs.push(key(vk, true));
            }
        }
        inputs.extend([key(VK_CONTROL, false), key(b'V' as u16, false), key(b'V' as u16, true), key(VK_CONTROL, true)]);
        std::thread::sleep(std::time::Duration::from_millis(25));
        SendInput(inputs.len() as u32, inputs.as_ptr(), std::mem::size_of::<INPUT>() as i32);
    }
}

fn choose(index: usize) {
    let (id, target) = {
        let st = STATE.lock().unwrap();
        match ordered_items(&st).get(index) {
            Some(item) => (item.id, st.target as HWND),
            None => return,
        }
    };
    let settings = app().settings.lock().unwrap().clone();
    let paste = settings.auto_paste;
    if !settings.sticky_popup { hide(); }
    if !restore(id, paste, target) {
        refresh();
    }
}

fn ordered_items(st: &State) -> Vec<&Summary> {
    st.items.iter().filter(|it| it.pinned).chain(st.items.iter().filter(|it| !it.pinned)).collect()
}

fn move_sel(delta: isize) {
    let mut st = STATE.lock().unwrap();
    if st.items.is_empty() {
        return;
    }
    let last = st.items.len() as isize - 1;
    st.sel = (st.sel as isize + delta).clamp(0, last) as usize;
    if st.sel < st.top {
        st.top = st.sel;
    } else if st.sel >= st.top + VISIBLE {
        st.top = st.sel + 1 - VISIBLE;
    }
}

fn kind_tag(kind: &str) -> &'static str {
    match kind {
        "text" => "글",
        "image" => "그림",
        "files" => "파일",
        _ => "?",
    }
}

struct PaintGuard {
    hwnd: HWND,
    ps: PAINTSTRUCT,
    hdc: HDC,
    mem: HDC,
    bmp: HBITMAP,
    old_bmp: HGDIOBJ,
    font: HFONT,
    small: HFONT,
    old_font: HGDIOBJ,
}

impl Drop for PaintGuard {
    fn drop(&mut self) {
        unsafe {
            if !self.mem.is_null() {
                if !self.old_font.is_null() {
                    SelectObject(self.mem, self.old_font);
                }
                if !self.old_bmp.is_null() {
                    SelectObject(self.mem, self.old_bmp);
                }
                DeleteDC(self.mem);
            }
            if !self.font.is_null() {
                DeleteObject(self.font);
            }
            if !self.small.is_null() {
                DeleteObject(self.small);
            }
            if !self.bmp.is_null() {
                DeleteObject(self.bmp);
            }
            if !self.hdc.is_null() {
                EndPaint(self.hwnd, &self.ps);
            }
        }
    }
}

unsafe fn paint(hwnd: HWND) {
    unsafe {
        let mut ps: PAINTSTRUCT = std::mem::zeroed();
        let hdc = BeginPaint(hwnd, &mut ps);
        if hdc.is_null() {
            return;
        }
        let mut guard = PaintGuard {
            hwnd,
            ps,
            hdc,
            mem: std::ptr::null_mut(),
            bmp: std::ptr::null_mut(),
            old_bmp: std::ptr::null_mut(),
            font: std::ptr::null_mut(),
            small: std::ptr::null_mut(),
            old_font: std::ptr::null_mut(),
        };

        let mut rc: RECT = std::mem::zeroed();
        GetClientRect(hwnd, &mut rc);
        let (w, h) = (rc.right, rc.bottom);
        let mem = CreateCompatibleDC(hdc);
        if mem.is_null() {
            return;
        }
        guard.mem = mem;

        let bmp = CreateCompatibleBitmap(hdc, w, h);
        if bmp.is_null() {
            return;
        }
        guard.bmp = bmp;
        guard.old_bmp = SelectObject(mem, bmp);

        let font = CreateFontW(-scale(hwnd, 15), 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, wide("맑은 고딕").as_ptr());
        let small = CreateFontW(-scale(hwnd, 12), 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, wide("맑은 고딕").as_ptr());
        if font.is_null() || small.is_null() {
            guard.font = font;
            guard.small = small;
            return;
        }
        guard.font = font;
        guard.small = small;
        guard.old_font = SelectObject(mem, font);
        SetBkMode(mem, TRANSPARENT as i32);

        let fill = |r: RECT, color: u32| {
            let brush = CreateSolidBrush(color);
            if !brush.is_null() {
                FillRect(mem, &r, brush);
                DeleteObject(brush);
            }
        };
        fill(rc, 0x00FFFFFF);
        let head = scale(hwnd, HEAD_H);
        fill(RECT { left: 0, top: 0, right: w, bottom: head }, 0x00F5EFE8);
        SelectObject(mem, small);
        SetTextColor(mem, 0x00555555);
        let pin_w = scale(hwnd, PIN_W);
        let pinned = { let s = app().settings.lock().unwrap(); s.sticky_popup && s.always_on_top };
        let close_w = scale(hwnd, CLOSE_W);
        let capture_w = scale(hwnd, CAPTURE_W);
        let clear_w = scale(hwnd, CLEAR_W);
        let collapse_w = scale(hwnd, COLLAPSE_W);
        let mut close = RECT { left: w - close_w, top: 0, right: w, bottom: head };
        SetTextColor(mem, 0x00555555);
        DrawTextW(mem, wide("✕").as_ptr(), -1, &mut close, DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
        let mut pin = RECT { left: w - close_w - pin_w, top: 0, right: w - close_w, bottom: head };
        fill(pin, if pinned { 0x00D9731F } else { 0x00E6DDD2 });
        SetTextColor(mem, if pinned { 0x00FFFFFF } else { 0x00555555 });
        DrawTextW(mem, wide(if pinned { "■ 항상 위" } else { "□ 항상 위" }).as_ptr(), -1, &mut pin,
                  DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
        let mut capture = RECT { left: pin.left - capture_w, top: 0, right: pin.left, bottom: head };
        fill(capture, 0x00E6DDD2);
        DrawTextW(mem, wide("캡처").as_ptr(), -1, &mut capture, DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
        let mut clear = RECT { left: capture.left - clear_w, top: 0, right: capture.left, bottom: head };
        fill(clear, 0x00E6DDD2);
        DrawTextW(mem, wide("지우기").as_ptr(), -1, &mut clear, DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
        let mut collapse = RECT { left: clear.left - collapse_w, top: 0, right: clear.left, bottom: head };
        fill(collapse, 0x00E6DDD2);
        let collapsed = app().settings.lock().unwrap().popup_collapsed;
        DrawTextW(mem, wide(if collapsed { "□" } else { "▁" }).as_ptr(), -1, &mut collapse,
                  DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
        SetTextColor(mem, 0x00555555);
        let mut hr = RECT { left: scale(hwnd, 10), top: 0, right: collapse.left - scale(hwnd, 6), bottom: head };
        let st = STATE.lock().unwrap();
        let title = if st.needle().is_empty() {
            "몽땅클립보드 · 드래그 이동 · 1~9 선택".to_string()
        } else {
            SetTextColor(mem, 0x00222222);
            format!("찾기: {}{}▏ · {}개 · Esc 지우기", st.query, st.comp, st.items.len())
        };
        DrawTextW(mem, wide(&title).as_ptr(), -1, &mut hr, DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX);

        let row = scale(hwnd, ROW_H);
        let collapsed = app().settings.lock().unwrap().popup_collapsed;
        if collapsed { drop(st); BitBlt(hdc, 0, 0, w, h, mem, 0, 0, SRCCOPY); return; }
        let visible_rows = ((h - head).max(0) / row).max(1) as usize;
        if st.items.is_empty() {
            SelectObject(mem, font);
            let mut r = RECT { left: scale(hwnd, 12), top: head, right: w, bottom: head + row };
            let t = wide(if st.needle().is_empty() { "아직 기록된 항목이 없습니다. 무엇이든 복사해 보세요." }
                         else { "찾는 글자가 들어 있는 항목이 없습니다." });
            DrawTextW(mem, t.as_ptr(), -1, &mut r, DT_SINGLELINE | DT_VCENTER);
        }
        let ordered = ordered_items(&st);
        for (i, item) in ordered.iter().enumerate().skip(st.top).take(visible_rows) {
            let y = head + (i - st.top) as i32 * row;
            let r = RECT { left: 0, top: y, right: w, bottom: y + row };
            if i == st.sel {
                fill(r, 0x00F7E3CF);
            } else if st.hover == Some(i) {
                fill(r, 0x00FBF3EC);
            }
            SelectObject(mem, small);
            SetTextColor(mem, 0x00EB6325);
            let shortcut = if i - st.top < 9 && st.needle().is_empty() { format!("{}", i - st.top + 1) } else { String::new() };
            let mut nr = RECT { left: scale(hwnd, 8), top: y, right: scale(hwnd, 24), bottom: y + row };
            DrawTextW(mem, wide(&shortcut).as_ptr(), -1, &mut nr, DT_SINGLELINE | DT_VCENTER | DT_CENTER);
            SetTextColor(mem, 0x00888888);
            let tag = format!("{}{}{}{}", if item.pinned { "★" } else { "" }, kind_tag(&item.kind),
                if item.preview.contains("웹 ·") { " · 웹" } else { "" },
                if item.preview.contains("서식 포함") { " · 서식 포함" } else { "" });
            let mut tr = RECT { left: scale(hwnd, 28), top: y, right: scale(hwnd, 70), bottom: y + row };
            DrawTextW(mem, wide(&tag).as_ptr(), -1, &mut tr, DT_SINGLELINE | DT_VCENTER);
            SelectObject(mem, font);
            SetTextColor(mem, 0x00222222);
            let actions = if st.hover == Some(i) { scale(hwnd, ROW_PIN_W + ROW_DELETE_W) } else { 0 };
            let mut pr = RECT { left: scale(hwnd, 72), top: y, right: w - actions - scale(hwnd, 10), bottom: y + row };
            DrawTextW(mem, wide(&item.preview).as_ptr(), -1, &mut pr,
                      DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX);
            if st.hover == Some(i) {
                let mut del = RECT { left: w - scale(hwnd, ROW_DELETE_W), top: y, right: w, bottom: y + row };
                let mut pin = RECT { left: del.left - scale(hwnd, ROW_PIN_W), top: y, right: del.left, bottom: y + row };
                SetTextColor(mem, 0x00555555);
                DrawTextW(mem, wide("✕").as_ptr(), -1, &mut del, DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
                DrawTextW(mem, wide(if item.pinned { "📌" } else { "📍" }).as_ptr(), -1, &mut pin,
                          DT_SINGLELINE | DT_VCENTER | DT_CENTER | DT_NOPREFIX);
            }
        }
        drop(st);
        BitBlt(hdc, 0, 0, w, h, mem, 0, 0, SRCCOPY);
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
enum HeadButton { Pin, Close, Capture, Clear, Collapse }

/// 창 안 좌표가 머리글의 어느 단추 위인지(폭·높이는 화면 배율을 적용한 값).
fn head_button(x: i32, y: i32, width: i32, pin_w: i32, close_w: i32, capture_w: i32, clear_w: i32, collapse_w: i32, head: i32) -> Option<HeadButton> {
    if y < 0 || y >= head || x >= width { return None; }
    if x >= width - close_w { return Some(HeadButton::Close); }
    if x >= width - close_w - pin_w { return Some(HeadButton::Pin); }
    if x >= width - close_w - pin_w - capture_w { return Some(HeadButton::Capture); }
    if x >= width - close_w - pin_w - capture_w - clear_w { return Some(HeadButton::Clear); }
    if x >= width - close_w - pin_w - capture_w - clear_w - collapse_w { return Some(HeadButton::Collapse); }
    None
}

fn row_action(x: i32, width: i32, pin_w: i32, delete_w: i32) -> Option<bool> {
    if x >= width || x < width - pin_w - delete_w { return None; }
    Some(x < width - delete_w) // true = pin, false = delete
}

/// '항상 위': 다른 창을 눌러도 닫히지 않고 맨 위에 남는다. 끄면 원래처럼 포커스를 잃을 때 닫힌다.
fn toggle_pin() {
    {
        let mut settings = app().settings.lock().unwrap();
        let on = !(settings.sticky_popup && settings.always_on_top);
        // 항상 위만 끄고 켠다. 창은 닫기 단추를 누를 때까지 그대로 둔다.
        settings.sticky_popup = true;
        settings.always_on_top = on;
    }
    crate::save_settings();
    apply_settings();
}

fn row_at(hwnd: HWND, lp: LPARAM) -> Option<usize> {
    let y = ((lp >> 16) & 0xFFFF) as i16 as i32;
    let head = scale(hwnd, HEAD_H);
    if y < head {
        return None;
    }
    let st = STATE.lock().unwrap();
    let i = st.top + ((y - head) / scale(hwnd, ROW_H)) as usize;
    (i < st.items.len()).then_some(i)
}

unsafe extern "system" fn wndproc(hwnd: HWND, msg: u32, wp: WPARAM, lp: LPARAM) -> LRESULT {
    unsafe {
        match msg {
            WM_PAINT => {
                paint(hwnd);
                0
            }
            WM_GETMINMAXINFO => {
                let info = &mut *(lp as *mut MINMAXINFO);
                info.ptMinTrackSize.x = scale(hwnd, MIN_W);
                // 접힌 창은 머리글 높이까지 줄어야 한다.
                let min_h = if app().settings.lock().unwrap().popup_collapsed { COLLAPSED_H } else { MIN_H };
                info.ptMinTrackSize.y = scale(hwnd, min_h);
                0
            }
            WM_ERASEBKGND => 1,
            WM_EXITSIZEMOVE if IsWindowVisible(hwnd) != 0 => {
                let mut rect: RECT = std::mem::zeroed();
                if GetWindowRect(hwnd, &mut rect) != 0 {
                    let dpi = GetDpiForWindow(hwnd).max(96) as i64;
                    let mut settings = app().settings.lock().unwrap();
                    settings.popup_x = rect.left as i64 * 96 / dpi;
                    settings.popup_y = rect.top as i64 * 96 / dpi;
                    settings.popup_width = (rect.right - rect.left) as i64 * 96 / dpi;
                    settings.popup_height = (rect.bottom - rect.top) as i64 * 96 / dpi;
                    drop(settings);
                    crate::save_settings();
                }
                0
            }
            WM_ACTIVATE if (wp & 0xFFFF) as u32 == WA_INACTIVE => {
                if !app().settings.lock().unwrap().sticky_popup { hide(); }
                0
            }
            WM_NCHITTEST => {
                let mut rect: RECT = std::mem::zeroed();
                GetWindowRect(hwnd, &mut rect);
                let screen_y = (lp >> 16) as i16 as i32;
                let screen_x = (lp & 0xFFFF) as i16 as i32;
                if head_button(screen_x - rect.left, screen_y - rect.top, rect.right - rect.left,
                               scale(hwnd, PIN_W), scale(hwnd, CLOSE_W), scale(hwnd, CAPTURE_W), scale(hwnd, CLEAR_W),
                               scale(hwnd, COLLAPSE_W), scale(hwnd, HEAD_H)).is_some() {
                    return HTCLIENT as LRESULT;
                }
                if screen_y >= rect.top && screen_y < rect.top + scale(hwnd, HEAD_H) {
                    HTCAPTION as LRESULT
                } else {
                    DefWindowProcW(hwnd, msg, wp, lp)
                }
            }
            WM_KEYDOWN => {
                let vk = wp as u16;
                match vk {
                    VK_ESCAPE => {
                        let searching = !STATE.lock().unwrap().needle().is_empty();
                        if searching {
                            let mut st = STATE.lock().unwrap();
                            st.query.clear();
                            st.comp.clear();
                            drop(st);
                            refilter();
                        } else {
                            hide();
                        }
                    }
                    VK_BACK => {
                        let changed = STATE.lock().unwrap().query.pop().is_some();
                        if changed {
                            refilter();
                        }
                    }
                    VK_RETURN => {
                        let sel = STATE.lock().unwrap().sel;
                        choose(sel);
                    }
                    VK_UP => move_sel(-1),
                    VK_DOWN => move_sel(1),
                    VK_PRIOR => move_sel(-(VISIBLE as isize)),
                    VK_NEXT => move_sel(VISIBLE as isize),
                    VK_HOME => move_sel(-100000),
                    VK_END => move_sel(100000),
                    VK_DELETE => {
                        let id = {
                            let st = STATE.lock().unwrap();
                            st.items.get(st.sel).map(|i| i.id)
                        };
                        if let Some(id) = id {
                            let _ = app().store.lock().unwrap().delete(id);
                            refresh_recent();
                            refresh();
                        }
                    }
                    0x31..=0x39 | 0x61..=0x69 if STATE.lock().unwrap().needle().is_empty() => {
                        let n = if vk >= 0x61 { vk - 0x61 } else { vk - 0x31 } as usize;
                        let top = STATE.lock().unwrap().top;
                        choose(top + n);
                        return 0;
                    }
                    _ => return 0,
                }
                InvalidateRect(hwnd, std::ptr::null(), 0);
                0
            }
            WM_CHAR => {
                let ch = char::from_u32(wp as u32).unwrap_or('\0');
                let mut st = STATE.lock().unwrap();
                // 찾기 전의 숫자는 고르기(WM_KEYDOWN)에 썼다. 제어 문자는 무시.
                if IsWindowVisible(hwnd) == 0 || ch < ' ' || ch == '\u{7f}'
                    || (st.needle().is_empty() && ch.is_ascii_digit() && ch != '0')
                    || st.query.chars().count() >= 40
                {
                    return 0;
                }
                st.query.push(ch);
                st.comp.clear();
                drop(st);
                refilter();
                0
            }
            WM_IME_COMPOSITION => {
                if lp as u32 & GCS_COMPSTR != 0 {
                    let imc = ImmGetContext(hwnd);
                    let bytes = ImmGetCompositionStringW(imc, GCS_COMPSTR, std::ptr::null_mut(), 0);
                    let mut buf = vec![0u16; (bytes.max(0) as usize) / 2];
                    if !buf.is_empty() {
                        ImmGetCompositionStringW(imc, GCS_COMPSTR, buf.as_mut_ptr() as _, bytes as u32);
                    }
                    ImmReleaseContext(hwnd, imc);
                    STATE.lock().unwrap().comp = String::from_utf16_lossy(&buf);
                    refilter();
                }
                // 확정 글자는 기본 처리가 WM_CHAR로 보낸다.
                DefWindowProcW(hwnd, msg, wp, lp)
            }
            WM_IME_ENDCOMPOSITION => {
                STATE.lock().unwrap().comp.clear();
                DefWindowProcW(hwnd, msg, wp, lp)
            }
            WM_MOUSEMOVE => {
                let i = row_at(hwnd, lp);
                let mut st = STATE.lock().unwrap();
                if st.hover != i {
                    st.hover = i;
                    drop(st);
                    InvalidateRect(hwnd, std::ptr::null(), 0);
                }
                0
            }
            WM_LBUTTONUP => {
                let mut rc: RECT = std::mem::zeroed();
                GetClientRect(hwnd, &mut rc);
                let (x, y) = ((lp & 0xFFFF) as i16 as i32, (lp >> 16) as i16 as i32);
                match head_button(x, y, rc.right, scale(hwnd, PIN_W), scale(hwnd, CLOSE_W), scale(hwnd, CAPTURE_W),
                                  scale(hwnd, CLEAR_W), scale(hwnd, COLLAPSE_W), scale(hwnd, HEAD_H)) {
                    Some(HeadButton::Pin) => { toggle_pin(); return 0; }
                    Some(HeadButton::Close) => { hide(); return 0; }
                    Some(HeadButton::Capture) => { hide(); crate::capture_screen(); return 0; }
                    Some(HeadButton::Clear) => { if crate::confirm_clear(hwnd) { let _ = app().store.lock().unwrap().clear(true); refresh_recent(); } return 0; }
                    Some(HeadButton::Collapse) => { let mut s = app().settings.lock().unwrap(); s.popup_collapsed = !s.popup_collapsed; let collapsed = s.popup_collapsed; drop(s); crate::save_settings(); // 폭은 그대로 두고 높이만 바꾼다. 설정 잠금은 SetWindowPos 전에 풀어야 한다(WM_GETMINMAXINFO가 다시 잠근다).
                        let saved_h = app().settings.lock().unwrap().popup_height as i32;
                        let target_h = if collapsed { COLLAPSED_H } else if saved_h > COLLAPSED_H { saved_h } else { HEAD_H + ROW_H * 5 + 8 };
                        let mut rect: RECT = std::mem::zeroed();
                        GetWindowRect(hwnd, &mut rect);
                        SetWindowPos(hwnd, std::ptr::null_mut(), 0, 0, rect.right - rect.left, scale(hwnd, target_h), SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE); InvalidateRect(hwnd, std::ptr::null(), 0); return 0; }
                    None => {}
                }
                if let Some(i) = row_at(hwnd, lp) {
                    let x = (lp & 0xFFFF) as i16 as i32;
                    let mut rc: RECT = std::mem::zeroed(); GetClientRect(hwnd, &mut rc);
                    let action_width = scale(hwnd, ROW_PIN_W + ROW_DELETE_W);
                    if STATE.lock().unwrap().hover == Some(i) && x >= rc.right - action_width {
                        let pinned = { let st = STATE.lock().unwrap(); st.items.get(i).map(|v| v.pinned).unwrap_or(false) };
                        if row_action(x, rc.right, scale(hwnd, ROW_PIN_W), scale(hwnd, ROW_DELETE_W)) == Some(true) {
                            let id = STATE.lock().unwrap().items[i].id;
                            let _ = app().store.lock().unwrap().pin(id, !pinned);
                        } else { let id = STATE.lock().unwrap().items[i].id; let _ = app().store.lock().unwrap().delete(id); }
                        refresh_recent(); refresh(); return 0;
                    }
                    choose(i);
                }
                0
            }
            WM_RBUTTONUP => {
                if let Some(i) = row_at(hwnd, lp) {
                    let item = {
                        let st = STATE.lock().unwrap();
                        ordered_items(&st).get(i).map(|v| (v.id, v.kind.clone(), v.preview.contains("웹 ·")))
                    };
                    if let Some((id, kind, web)) = item {
                        let mut pt = POINT { x: (lp & 0xffff) as i16 as i32, y: (lp >> 16) as i16 as i32 };
                        ClientToScreen(hwnd, &mut pt);
                        let menu = CreatePopupMenu();
                        if !menu.is_null() {
                            AppendMenuW(menu, MF_STRING, 1, wide("열기").as_ptr());
                            if web {
                                if kind == "text" { AppendMenuW(menu, MF_STRING, 3, wide("글을 연결 프로그램으로 열기").as_ptr()); }
                            } else {
                                AppendMenuW(menu, MF_STRING, 2, wide("연결 프로그램 선택…").as_ptr());
                            }
                            let command = TrackPopupMenu(menu, TPM_RETURNCMD | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, std::ptr::null());
                            DestroyMenu(menu);
                            if command == 1 || command == 2 || command == 3 {
                                let payload = app().store.lock().unwrap().payload(id).ok().flatten();
                                if let Some((_, data, extra)) = payload {
                                    if command == 3 {
                                        if restore(id, false, std::ptr::null_mut()) {
                                            open_item::open(hwnd, &app().dir, "text", &data, &[], true);
                                        }
                                    } else { open_item::open(hwnd, &app().dir, &kind, &data, &extra, command == 2); }
                                }
                            }
                        }
                    }
                }
                0
            }
            WM_MOUSEWHEEL => {
                let delta = ((wp >> 16) & 0xFFFF) as i16;
                move_sel(if delta > 0 { -3 } else { 3 });
                InvalidateRect(hwnd, std::ptr::null(), 0);
                0
            }
            _ => DefWindowProcW(hwnd, msg, wp, lp),
        }
    }
}

#[cfg(test)]
mod head_button_tests {
    use super::*;

    #[test]
    fn close_is_rightmost_then_pin_then_title() {
        assert_eq!(head_button(599, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Close));
        assert_eq!(head_button(570, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Close));
        assert_eq!(head_button(539, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Pin));
        assert_eq!(head_button(493, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Capture));
        assert_eq!(head_button(465, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Capture));
        assert_eq!(head_button(409, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Clear));
        assert_eq!(head_button(365, 5, 600, 76, 30, 54, 54, 34, 30), Some(HeadButton::Collapse));
    }

    #[test]
    fn rows_below_header_are_not_buttons() {
        assert_eq!(head_button(599, 30, 600, 76, 30, 54, 54, 34, 30), None);
    }

    #[test]
    fn header_button_hit_regions_do_not_overlap() {
        let args = (600, 76, 30, 54, 54, 34, 30);
        assert_eq!(head_button(599, 10, args.0, args.1, args.2, args.3, args.4, args.5, args.6), Some(HeadButton::Close));
        assert_eq!(head_button(539, 10, args.0, args.1, args.2, args.3, args.4, args.5, args.6), Some(HeadButton::Pin));
        assert_eq!(head_button(493, 10, args.0, args.1, args.2, args.3, args.4, args.5, args.6), Some(HeadButton::Capture));
        assert_eq!(head_button(439, 10, args.0, args.1, args.2, args.3, args.4, args.5, args.6), Some(HeadButton::Clear));
        assert_eq!(head_button(385, 10, args.0, args.1, args.2, args.3, args.4, args.5, args.6), Some(HeadButton::Collapse));
    }

    #[test]
    fn hover_actions_reserve_right_side_only() {
        assert_eq!(row_action(543, 600, 28, 28), None);
        assert_eq!(row_action(544, 600, 28, 28), Some(true));
        assert_eq!(row_action(572, 600, 28, 28), Some(false));
        assert_eq!(row_action(600, 600, 28, 28), None);
    }
}
