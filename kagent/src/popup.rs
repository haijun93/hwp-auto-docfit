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
use crate::util::wide;
use crate::{app, main_hwnd, refresh_recent, restore};

const CLASS: &str = "HwpAutoDocFit.KAgentPopup";
const VISIBLE: usize = 12;
const BASE_W: i32 = 440;
const ROW_H: i32 = 30;
const HEAD_H: i32 = 30;

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
        let hwnd = CreateWindowExW(WS_EX_TOPMOST | WS_EX_TOOLWINDOW, class.as_ptr(), wide("K클립보드").as_ptr(),
                                   WS_POPUP | WS_BORDER, 0, 0, BASE_W, 200, std::ptr::null_mut(),
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
        let (w, h) = (scale(hwnd, BASE_W), scale(hwnd, HEAD_H + ROW_H * rows + 8));
        let monitor = MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
        let mut mi: MONITORINFO = std::mem::zeroed();
        mi.cbSize = std::mem::size_of::<MONITORINFO>() as u32;
        GetMonitorInfoW(monitor, &mut mi);
        let wa = mi.rcWork;
        let x = (pt.x + 8).min(wa.right - w).max(wa.left);
        let y = (pt.y + 8).min(wa.bottom - h).max(wa.top);
        SetWindowPos(hwnd, HWND_TOPMOST, x, y, w, h, SWP_SHOWWINDOW);
        SetForegroundWindow(hwnd);
        SetFocus(hwnd);
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
        match st.items.get(index) {
            Some(item) => (item.id, st.target as HWND),
            None => return,
        }
    };
    let paste = app().settings.lock().unwrap().auto_paste;
    hide();
    if !restore(id, paste, target) {
        refresh();
    }
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
        let mut hr = RECT { left: scale(hwnd, 10), top: 0, right: w - scale(hwnd, 10), bottom: head };
        let st = STATE.lock().unwrap();
        let title = if st.needle().is_empty() {
            "K클립보드 · 1~9 또는 ↑↓ Enter · 글자를 치면 찾기 · Esc 닫기".to_string()
        } else {
            SetTextColor(mem, 0x00222222);
            format!("찾기: {}{}▏ · {}개 · Esc 지우기", st.query, st.comp, st.items.len())
        };
        DrawTextW(mem, wide(&title).as_ptr(), -1, &mut hr, DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX);

        let row = scale(hwnd, ROW_H);
        if st.items.is_empty() {
            SelectObject(mem, font);
            let mut r = RECT { left: scale(hwnd, 12), top: head, right: w, bottom: head + row };
            let t = wide(if st.needle().is_empty() { "아직 기록된 항목이 없습니다. 무엇이든 복사해 보세요." }
                         else { "찾는 글자가 들어 있는 항목이 없습니다." });
            DrawTextW(mem, t.as_ptr(), -1, &mut r, DT_SINGLELINE | DT_VCENTER);
        }
        for (i, item) in st.items.iter().enumerate().skip(st.top).take(VISIBLE) {
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
            let tag = format!("{}{}", if item.pinned { "★" } else { "" }, kind_tag(&item.kind));
            let mut tr = RECT { left: scale(hwnd, 28), top: y, right: scale(hwnd, 70), bottom: y + row };
            DrawTextW(mem, wide(&tag).as_ptr(), -1, &mut tr, DT_SINGLELINE | DT_VCENTER);
            SelectObject(mem, font);
            SetTextColor(mem, 0x00222222);
            let mut pr = RECT { left: scale(hwnd, 72), top: y, right: w - scale(hwnd, 10), bottom: y + row };
            DrawTextW(mem, wide(&item.preview).as_ptr(), -1, &mut pr,
                      DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX);
        }
        drop(st);
        BitBlt(hdc, 0, 0, w, h, mem, 0, 0, SRCCOPY);
    }
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
            WM_ERASEBKGND => 1,
            WM_ACTIVATE if (wp & 0xFFFF) as u32 == WA_INACTIVE => {
                hide();
                0
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
                if let Some(i) = row_at(hwnd, lp) {
                    choose(i);
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
