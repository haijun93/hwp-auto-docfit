//! 빠른 붙여넣기 팝업: 단축키를 누르면 마우스 옆에 최근 항목을 바로 그린다(메모리 목록, DB 읽기 없음).
//! 숫자 1~9·↑↓·Enter로 고르면 원래 창으로 돌아가 붙여넣는다. Esc·바깥 클릭은 닫기.
//!
//! 화면 구성(2026-11-07 개편):
//! ① 상단 메뉴바: 왼쪽 '몽땅클립보드', 오른쪽에 화면캡처 · 항상 위(켜짐 표시) · 최소화 · 최대화/복원 · 닫기.
//!    오른쪽 세 단추는 Windows 캡션 단추와 같은 폭(46)·글리프(Segoe MDL2 Assets)·마우스 올림 색(닫기는 빨강).
//!    단추를 눌러도 창이 활성화되지 않는다(WM_MOUSEACTIVATE → MA_NOACTIVATE, 붙여넣을 창의 포커스 유지).
//!    최소화: 작업 표시줄 단추가 없는 도구 창이므로 창을 숨기고 분류·찾기·선택 상태를 그대로 둔다.
//!    단축키·트레이로 다시 부르면 그 상태로 다시 보인다. 최대화는 모니터 작업 영역, 다시 누르면 이전 크기.
//!    머리글 두 번 클릭 = 최대화/복원. 모두 지우기·접기는 머리글·항목의 오른쪽 클릭 메뉴로 옮겼다.
//! ② 분류 메뉴바: 전체·문서·그림·파일·폴더·웹·화면캡처·키워드검색(기본 '전체', 열 때마다 전체).
//!    분류는 메모리 목록(최근 RECENT개, 항목별 분류는 저장소가 계산해 둠)에서 바로 거르고,
//!    메모리 목록이 꽉 차 있어 더 오래된 항목이 있을 수 있으면 저장소에서 같은 분류를 최대 50개까지 더 찾는다.
//!    키워드검색은 저장된 모든 항목 대상(한글 조합 중 글자 포함, 파일 전체 경로·웹 주소 포함).
//!    아무 분류에서나 글자를 치면 키워드검색으로 넘어간다. ←→·Tab(Shift+Tab)으로 분류 이동, Ctrl+F는 키워드검색.
//!    좁은 폭에서는 단추 여백을 줄이고, 그래도 넘치면 짧은 이름(캡처·검색), 마지막엔 같은 폭으로 나눠 말줄임.
//! 목록 순서: 고정 항목 먼저, 그 안과 나머지는 최근 사용 순(최신순).

use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, AtomicIsize, Ordering};

use windows_sys::Win32::Foundation::{HINSTANCE, HWND, LPARAM, LRESULT, POINT, RECT, SIZE, WPARAM};
use windows_sys::Win32::Graphics::Gdi::*;
use windows_sys::Win32::UI::HiDpi::GetDpiForWindow;
use windows_sys::Win32::UI::Input::Ime::{GCS_COMPSTR, ImmGetCompositionStringW, ImmGetContext, ImmReleaseContext};
use windows_sys::Win32::UI::Input::KeyboardAndMouse::{
    GetAsyncKeyState, GetKeyState, SetFocus, TrackMouseEvent, INPUT, INPUT_0, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP,
    SendInput, TME_LEAVE, TRACKMOUSEEVENT, VIRTUAL_KEY, VK_BACK, VK_CONTROL, VK_DELETE, VK_DOWN, VK_END, VK_ESCAPE,
    VK_HOME, VK_LEFT, VK_LMENU, VK_LWIN, VK_MENU, VK_NEXT, VK_PRIOR, VK_RETURN, VK_RIGHT, VK_RMENU, VK_RWIN, VK_SHIFT,
    VK_TAB, VK_UP,
};
use windows_sys::Win32::UI::WindowsAndMessaging::*;

use crate::category::Category;
use crate::store::Summary;
use crate::open_item;
use crate::util::wide;
use crate::{app, main_hwnd, refresh_recent, restore};

const CLASS: &str = "HwpAutoDocFit.KAgentPopup";
const VISIBLE: usize = 12;
const BASE_W: i32 = 440;
const ROW_H: i32 = 30;
/// 상단 메뉴바 높이(Windows 11 캡션 높이와 같게).
const HEAD_H: i32 = 32;
/// 분류 메뉴바 높이.
const CAT_H: i32 = 28;
/// 캡션 단추 하나의 폭(Windows 기본 캡션 단추 46px).
const CAPTION_W: i32 = 46;
/// 접힌 창 높이. 두꺼운 틀 안쪽에 머리글이 다 보이도록 틀 높이를 더한다.
const COLLAPSED_H: i32 = HEAD_H + 12;
const ROW_PIN_W: i32 = 28;
const ROW_DELETE_W: i32 = 28;
/// 최소 폭: 제목(약 90) + 캡션 단추 5개(230).
const MIN_W: i32 = 320;
const MIN_H: i32 = HEAD_H + CAT_H + ROW_H * 2 + 12;
const TAB_MARGIN: i32 = 6;
const TAB_PAD: i32 = 9;
const TAB_MIN_PAD: i32 = 4;
/// 분류 보충·키워드검색 결과 상한.
const LIST_LIMIT: usize = 50;
/// WM_MOUSELEAVE(0x02A3). windows-sys에서는 Win32_UI_Controls 기능에만 있어 의존성 기능을 늘리지 않고 직접 둔다.
const WM_MOUSELEAVE: u32 = 0x02A3;
const CMD_COLLAPSE: usize = 10;
const CMD_CLEAR: usize = 11;

// ---- 분류 메뉴 ----

#[derive(Clone, Copy, PartialEq, Debug)]
enum Tab {
    Cat(Category),
    Search,
}

const TABS: [Tab; 8] = [
    Tab::Cat(Category::All), Tab::Cat(Category::Document), Tab::Cat(Category::Image), Tab::Cat(Category::File),
    Tab::Cat(Category::Folder), Tab::Cat(Category::Web), Tab::Cat(Category::Capture), Tab::Search,
];
const SEARCH_TAB: usize = TABS.len() - 1;

impl Tab {
    fn label(self, short: bool) -> &'static str {
        match self {
            Tab::Cat(Category::Capture) if short => "캡처",
            Tab::Cat(c) => c.label(),
            Tab::Search if short => "검색",
            Tab::Search => "키워드검색",
        }
    }
}

/// 분류 단추 배치(순수 함수). long·short: 각 단추 글자 폭(긴 이름·짧은 이름), avail: 쓸 수 있는 폭.
/// 돌려주는 값: 각 단추의 (왼쪽, 오른쪽)(0부터), 짧은 이름을 쓰는지.
/// 순서: ① 기본 여백 ② 최소 여백 ③ 짧은 이름+최소 여백 ④ 같은 폭으로 나눔(글자는 말줄임).
fn tab_layout(long: &[i32], short: &[i32], avail: i32, pad: i32, min_pad: i32) -> (Vec<(i32, i32)>, bool) {
    let lay = |widths: &[i32], p: i32| -> Option<Vec<(i32, i32)>> {
        let total: i32 = widths.iter().map(|w| w + 2 * p).sum();
        if total > avail {
            return None;
        }
        let mut x = 0;
        Some(widths.iter().map(|w| { let l = x; x += w + 2 * p; (l, x) }).collect())
    };
    if let Some(v) = lay(long, pad) { return (v, false); }
    if let Some(v) = lay(long, min_pad) { return (v, false); }
    if let Some(v) = lay(short, min_pad) { return (v, true); }
    let n = long.len().max(1) as i32;
    let avail = avail.max(0);
    let spans = (0..n).map(|i| (avail * i / n, avail * (i + 1) / n)).collect();
    (spans, true)
}

/// x가 어느 분류 단추 위인지.
fn tab_at(x: i32, spans: &[(i32, i32)]) -> Option<usize> {
    spans.iter().position(|&(l, r)| x >= l && x < r)
}

/// 분류를 delta만큼 옮긴다(양 끝에서 돌아간다).
fn next_tab(cur: usize, delta: isize) -> usize {
    let n = TABS.len() as isize;
    ((cur as isize + delta).rem_euclid(n)) as usize
}

// ---- 상단 메뉴바 단추 ----

#[derive(Clone, Copy, PartialEq, Debug)]
enum HeadButton { Capture, Pin, Minimize, Maximize, Close }

/// 왼쪽부터 놓이는 순서. 모두 같은 폭이고 닫기가 맨 오른쪽.
const HEAD_BUTTONS: [HeadButton; 5] =
    [HeadButton::Capture, HeadButton::Pin, HeadButton::Minimize, HeadButton::Maximize, HeadButton::Close];

/// 단추의 가로 범위(창 안 좌표, 화면 배율 적용한 폭).
fn head_button_span(b: HeadButton, width: i32, button_w: i32) -> (i32, i32) {
    let i = HEAD_BUTTONS.iter().position(|x| *x == b).unwrap_or(0) as i32;
    let from_right = HEAD_BUTTONS.len() as i32 - i;
    let left = width - from_right * button_w;
    (left, left + button_w)
}

/// 창 안 좌표가 상단 메뉴바의 어느 단추 위인지.
fn head_button(x: i32, y: i32, width: i32, button_w: i32, head: i32) -> Option<HeadButton> {
    if y < 0 || y >= head || x < 0 || x >= width {
        return None;
    }
    HEAD_BUTTONS.iter().copied().find(|b| {
        let (l, r) = head_button_span(*b, width, button_w);
        x >= l && x < r
    })
}

/// 단추 이름(접근성·마우스 올림 안내).
fn head_button_name(b: HeadButton, pinned: bool, maximized: bool) -> &'static str {
    match b {
        HeadButton::Capture => "화면 캡처",
        HeadButton::Pin if pinned => "항상 위 끄기 (켜짐)",
        HeadButton::Pin => "항상 위 켜기",
        HeadButton::Minimize => "최소화 (단축키로 다시 열기)",
        HeadButton::Maximize if maximized => "이전 크기로 복원",
        HeadButton::Maximize => "최대화",
        HeadButton::Close => "닫기",
    }
}

/// Segoe MDL2 Assets 글리프(Windows 캡션 단추와 같은 기호).
fn head_button_glyph(b: HeadButton, pinned: bool, maximized: bool) -> char {
    match b {
        HeadButton::Capture => '\u{E722}',                   // Camera
        HeadButton::Pin => if pinned { '\u{E840}' } else { '\u{E718}' }, // Pinned / Pin
        HeadButton::Minimize => '\u{E921}',                  // ChromeMinimize
        HeadButton::Maximize => if maximized { '\u{E923}' } else { '\u{E922}' }, // ChromeRestore / ChromeMaximize
        HeadButton::Close => '\u{E8BB}',                     // ChromeClose
    }
}

// ---- 목록 배치 ----

/// 목록 첫 줄의 y(머리글 + 분류 메뉴바 + 키워드검색이면 입력 줄).
fn list_top(head: i32, cat: i32, search_row: bool, row: i32) -> i32 {
    head + cat + if search_row { row } else { 0 }
}

/// y가 가리키는 항목 위치(스크롤 top 반영). 목록 밖이면 None.
fn row_index(y: i32, top_y: i32, row_h: i32, scroll_top: usize, len: usize) -> Option<usize> {
    if y < top_y || row_h <= 0 {
        return None;
    }
    let i = scroll_top + ((y - top_y) / row_h) as usize;
    (i < len).then_some(i)
}

fn row_action(x: i32, width: i32, pin_w: i32, delete_w: i32) -> Option<bool> {
    if x >= width || x < width - pin_w - delete_w { return None; }
    Some(x < width - delete_w) // true = pin, false = delete
}

/// 고정 항목을 먼저, 그 안과 나머지는 받은 순서(최근 사용 순)를 유지한다.
fn order_items(items: Vec<Summary>) -> Vec<Summary> {
    let (mut pinned, rest): (Vec<_>, Vec<_>) = items.into_iter().partition(|i| i.pinned);
    pinned.extend(rest);
    pinned
}

/// 메모리 목록에서 분류로 거른다(키워드검색 칸은 거르지 않음).
fn filter_memory(items: &[Summary], tab: Tab) -> Vec<Summary> {
    match tab {
        Tab::Cat(c) => items.iter().filter(|i| i.cats.contains(c)).cloned().collect(),
        Tab::Search => items.to_vec(),
    }
}

/// 저장소를 더 볼지: 찾기 글자가 있으면 항상(모든 항목 대상), 분류는 메모리 목록이 꽉 차 있는데
/// 거른 결과가 상한보다 적을 때만(더 오래된 같은 분류 항목이 있을 수 있음). '전체'는 메모리 목록 그대로.
fn needs_store(tab: Tab, memory_len: usize, filtered_len: usize, needle_empty: bool) -> bool {
    match tab {
        Tab::Search => !needle_empty,
        Tab::Cat(Category::All) => false,
        Tab::Cat(_) => memory_len >= crate::RECENT && filtered_len < LIST_LIMIT,
    }
}

// ---- 상태 ----

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
    /// 고른 분류(TABS 위치).
    tab: usize,
    /// 마지막으로 그린 분류 단추 범위(창 안 x) — 클릭 판정용.
    tab_spans: Vec<(i32, i32)>,
    hover_btn: Option<HeadButton>,
    pressed_btn: Option<HeadButton>,
    hover_tab: Option<usize>,
    /// 최대화 중이면 이전 창 위치.
    restore_rect: Option<RECT>,
    /// 최소화(숨김) 상태 — 다시 부르면 상태를 그대로 보여 준다.
    minimized: bool,
}

static STATE: Mutex<State> = Mutex::new(State {
    items: Vec::new(), sel: 0, top: 0, target: 0, hover: None, query: String::new(), comp: String::new(), seq: 0,
    tab: 0, tab_spans: Vec::new(), hover_btn: None, pressed_btn: None, hover_tab: None, restore_rect: None,
    minimized: false,
});
static TRACKING: AtomicBool = AtomicBool::new(false);

impl State {
    fn needle(&self) -> String {
        format!("{}{}", self.query, self.comp)
    }
    fn current(&self) -> Tab {
        TABS[self.tab.min(TABS.len() - 1)]
    }
}

/// 새 목록을 넣는다. 그사이 입력이 바뀌었으면(seq·찾기 글자) 버린다.
fn apply_items(seq: u64, needle: &str, items: Vec<Summary>, keep_sel: bool) -> bool {
    let mut st = STATE.lock().unwrap();
    if st.seq != seq || st.needle() != needle {
        return false;
    }
    let prev = if keep_sel { st.items.get(st.sel).map(|i| i.id) } else { None };
    st.items = order_items(items);
    if keep_sel {
        let len = st.items.len();
        st.sel = prev.and_then(|id| st.items.iter().position(|i| i.id == id)).unwrap_or(st.sel.min(len.saturating_sub(1)));
        st.top = st.top.min(st.sel);
    } else {
        st.sel = 0;
        st.top = 0;
    }
    st.hover = None;
    true
}

/// 분류·찾기 글자로 목록을 다시 만든다. 먼저 메모리 목록으로 바로 그리고, 필요할 때만 저장소를 본다.
/// 단계별로 잠금을 풀어 STATE와 DB/recent를 동시에 잡지 않고, seq로 늦게 온 결과가 새 입력을 덮지 않게 한다.
fn refilter(keep_sel: bool) {
    let (tab, needle, cur_seq) = {
        let mut st = STATE.lock().unwrap();
        st.seq += 1;
        (st.current(), st.needle(), st.seq)
    };
    let needle_empty = needle.trim().is_empty();
    let memory = app().recent.lock().unwrap().clone();
    let mut filtered_len = 0;
    if tab != Tab::Search || needle_empty {
        let items = filter_memory(&memory, tab);
        filtered_len = items.len();
        if !apply_items(cur_seq, &needle, items, keep_sel) {
            return;
        }
        unsafe {
            InvalidateRect(popup_hwnd(), std::ptr::null(), 0);
            UpdateWindow(popup_hwnd());
        }
    }
    if needs_store(tab, memory.len(), filtered_len, needle_empty) {
        let (cat, query) = match tab {
            Tab::Cat(c) => (c, ""),
            Tab::Search => (Category::All, needle.trim()),
        };
        let items = app().store.lock().unwrap().list(LIST_LIMIT, cat, query).unwrap_or_default();
        if apply_items(cur_seq, &needle, items, keep_sel) {
            unsafe { InvalidateRect(popup_hwnd(), std::ptr::null(), 0) };
        }
    }
}

fn set_tab(index: usize) {
    {
        let mut st = STATE.lock().unwrap();
        if st.tab == index {
            return;
        }
        if st.current() == Tab::Search {
            st.query.clear();
            st.comp.clear();
        }
        st.tab = index;
    }
    refilter(false);
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
/// 최소화해 둔 창이면 위치·분류·찾기 상태를 그대로 다시 보인다.
pub fn show() {
    let hwnd = popup_hwnd();
    if hwnd.is_null() {
        return;
    }
    unsafe {
        let settings = app().settings.lock().unwrap().clone();
        if settings.sticky_popup && IsWindowVisible(hwnd) != 0 {
            ShowWindow(hwnd, SW_HIDE);
            return;
        }
        let fg = GetForegroundWindow();
        let minimized = {
            let mut st = STATE.lock().unwrap();
            if fg != hwnd && fg != main_hwnd() {
                st.target = fg as isize;
            }
            std::mem::replace(&mut st.minimized, false)
        };
        if minimized {
            SetWindowPos(hwnd, if settings.always_on_top { HWND_TOPMOST } else { HWND_NOTOPMOST }, 0, 0, 0, 0,
                         SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
            SetForegroundWindow(hwnd);
            SetFocus(hwnd);
            refilter(true);
            return;
        }
        {
            let mut st = STATE.lock().unwrap();
            st.tab = 0; // 요구: 열 때 기본값은 '전체'
            st.query.clear();
            st.comp.clear();
            st.restore_rect = None;
            st.hover_btn = None;
            st.pressed_btn = None;
            st.hover_tab = None;
        }
        refilter(false);
        // 찾기 결과가 늘 수 있으므로 항목이 적어도 창은 몇 줄 여유를 둔다.
        let rows = STATE.lock().unwrap().items.len().clamp(5, VISIBLE) as i32;
        let mut pt = POINT { x: 0, y: 0 };
        GetCursorPos(&mut pt);
        // 창을 그 모니터의 DPI로 먼저 옮긴 뒤 크기를 정한다.
        SetWindowPos(hwnd, std::ptr::null_mut(), pt.x, pt.y, 1, 1, SWP_NOZORDER | SWP_NOACTIVATE);
        let (default_w, default_h) = (scale(hwnd, BASE_W), scale(hwnd, HEAD_H + CAT_H + ROW_H * rows + 8));
        let monitor = MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
        let mut mi: MONITORINFO = std::mem::zeroed();
        mi.cbSize = std::mem::size_of::<MONITORINFO>() as u32;
        GetMonitorInfoW(monitor, &mut mi);
        let wa = mi.rcWork;
        let (sticker, collapsed, saved_x, saved_y, saved_w, saved_h) =
            (settings.sticky_popup, settings.popup_collapsed, settings.popup_x, settings.popup_y,
             settings.popup_width, settings.popup_height);
        let dpi = GetDpiForWindow(hwnd).max(96) as i64;
        let saved_x_px = saved_x * dpi / 96;
        let saved_y_px = saved_y * dpi / 96;
        let saved_w_px = saved_w * dpi / 96;
        let saved_h_px = saved_h * dpi / 96;
        let saved_rect_valid = sticker && saved_x_px >= wa.left as i64 && saved_y_px >= wa.top as i64
            && saved_w > 0 && saved_h > COLLAPSED_H as i64
            && saved_x_px + saved_w_px <= wa.right as i64 && saved_y_px + saved_h_px <= wa.bottom as i64;
        let (x, y, w, mut h) = if saved_rect_valid {
            (saved_x_px as i32, saved_y_px as i32, saved_w_px as i32, saved_h_px as i32)
        } else {
            ((pt.x + 8).min(wa.right - default_w).max(wa.left),
             (pt.y + 8).min(wa.bottom - default_h).max(wa.top), default_w, default_h)
        };
        if collapsed {
            h = scale(hwnd, COLLAPSED_H);
        } else if h < scale(hwnd, MIN_H) {
            // 펼친 상태인데 높이가 너무 작으면(접힌 높이가 저장된 경우) 기본 높이로 되돌린다.
            h = default_h;
        }
        SetWindowPos(hwnd, if settings.always_on_top { HWND_TOPMOST } else { HWND_NOTOPMOST },
                     x, y, w.max(scale(hwnd, MIN_W)), h, SWP_SHOWWINDOW);
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

/// 목록이 바뀌면(보이는 동안) 같은 분류·찾기로 다시 거른다(선택한 항목 유지).
pub fn refresh() {
    let hwnd = popup_hwnd();
    if hwnd.is_null() || unsafe { IsWindowVisible(hwnd) } == 0 {
        return;
    }
    refilter(true);
}

/// 닫기: 숨기고 다음에 열 때 처음 상태(전체)로.
fn hide() {
    STATE.lock().unwrap().minimized = false;
    unsafe { ShowWindow(popup_hwnd(), SW_HIDE) };
}

/// 최소화: 숨기되 분류·찾기·선택·위치를 그대로 둔다.
fn minimize() {
    unsafe { ShowWindow(popup_hwnd(), SW_HIDE) };
    // 숨기는 동안 WM_ACTIVATE(비활성)가 hide()를 부를 수 있으므로 숨긴 뒤에 표시한다.
    STATE.lock().unwrap().minimized = true;
}

/// 최대화(모니터 작업 영역) ↔ 이전 크기.
fn toggle_max(hwnd: HWND) {
    let prev = STATE.lock().unwrap().restore_rect.take();
    unsafe {
        if let Some(r) = prev {
            SetWindowPos(hwnd, std::ptr::null_mut(), r.left, r.top, r.right - r.left, r.bottom - r.top,
                         SWP_NOZORDER | SWP_NOACTIVATE);
        } else {
            let mut r: RECT = std::mem::zeroed();
            GetWindowRect(hwnd, &mut r);
            let mut mi: MONITORINFO = std::mem::zeroed();
            mi.cbSize = std::mem::size_of::<MONITORINFO>() as u32;
            GetMonitorInfoW(MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST), &mut mi);
            let wa = mi.rcWork;
            STATE.lock().unwrap().restore_rect = Some(r);
            SetWindowPos(hwnd, std::ptr::null_mut(), wa.left, wa.top, wa.right - wa.left, wa.bottom - wa.top,
                         SWP_NOZORDER | SWP_NOACTIVATE);
        }
        InvalidateRect(hwnd, std::ptr::null(), 0);
    }
}

/// 목록 접기/펼치기(머리글만 남김). 오른쪽 클릭 메뉴에서 부른다.
fn toggle_collapse(hwnd: HWND) {
    let (collapsed, saved_h) = {
        let mut s = app().settings.lock().unwrap();
        s.popup_collapsed = !s.popup_collapsed;
        (s.popup_collapsed, s.popup_height as i32)
    };
    crate::save_settings();
    // 설정 잠금은 SetWindowPos 전에 풀어야 한다(WM_GETMINMAXINFO가 다시 잠근다).
    let target_h = if collapsed { COLLAPSED_H } else if saved_h >= MIN_H { saved_h } else { HEAD_H + CAT_H + ROW_H * 5 + 8 };
    STATE.lock().unwrap().restore_rect = None;
    unsafe {
        let mut rect: RECT = std::mem::zeroed();
        GetWindowRect(hwnd, &mut rect);
        SetWindowPos(hwnd, std::ptr::null_mut(), 0, 0, rect.right - rect.left, scale(hwnd, target_h),
                     SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);
        InvalidateRect(hwnd, std::ptr::null(), 0);
    }
}

fn clear_all(hwnd: HWND) {
    if crate::confirm_clear(hwnd) {
        let _ = app().store.lock().unwrap().clear(true);
        refresh_recent();
    }
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
    let settings = app().settings.lock().unwrap().clone();
    let paste = settings.auto_paste;
    if !settings.sticky_popup { hide(); }
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
    old_font: HGDIOBJ,
    fonts: Vec<HFONT>,
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
            for f in &self.fonts {
                if !f.is_null() {
                    DeleteObject(*f);
                }
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

unsafe fn text_width(dc: HDC, s: &str) -> i32 {
    let w: Vec<u16> = s.encode_utf16().collect();
    let mut size = SIZE { cx: 0, cy: 0 };
    unsafe { GetTextExtentPoint32W(dc, w.as_ptr(), w.len() as i32, &mut size) };
    size.cx
}

const ACCENT: u32 = 0x00D9731F; // BGR — 파랑(#1F73D9)
const HEAD_BG: u32 = 0x00F5EFE8;

unsafe fn paint(hwnd: HWND) {
    unsafe {
        let mut ps: PAINTSTRUCT = std::mem::zeroed();
        let hdc = BeginPaint(hwnd, &mut ps);
        if hdc.is_null() {
            return;
        }
        let mut guard = PaintGuard {
            hwnd, ps, hdc, mem: std::ptr::null_mut(), bmp: std::ptr::null_mut(), old_bmp: std::ptr::null_mut(),
            old_font: std::ptr::null_mut(), fonts: Vec::new(),
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

        let mk = |px: i32, weight: i32, face: &str| {
            CreateFontW(-scale(hwnd, px), 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 5, 0, wide(face).as_ptr())
        };
        let font = mk(15, 400, "맑은 고딕");
        let small = mk(12, 400, "맑은 고딕");
        let small_bold = mk(12, 700, "맑은 고딕");
        let title_font = mk(13, 700, "맑은 고딕");
        let glyph = mk(10, 400, "Segoe MDL2 Assets");
        let glyph_big = mk(14, 400, "Segoe MDL2 Assets");
        guard.fonts = vec![font, small, small_bold, title_font, glyph, glyph_big];
        if guard.fonts.iter().any(|f| f.is_null()) {
            return;
        }
        guard.old_font = SelectObject(mem, font);
        SetBkMode(mem, TRANSPARENT as i32);

        let fill = |r: RECT, color: u32| {
            let brush = CreateSolidBrush(color);
            if !brush.is_null() {
                FillRect(mem, &r, brush);
                DeleteObject(brush);
            }
        };
        let draw = |s: &str, r: RECT, flags: u32| {
            let mut r = r;
            DrawTextW(mem, wide(s).as_ptr(), -1, &mut r, flags | DT_SINGLELINE | DT_VCENTER | DT_NOPREFIX);
        };
        let pinned = { let s = app().settings.lock().unwrap(); s.sticky_popup && s.always_on_top };
        let head = scale(hwnd, HEAD_H);
        let cat_h = scale(hwnd, CAT_H);
        let row = scale(hwnd, ROW_H);
        let bw = scale(hwnd, CAPTION_W);
        fill(rc, 0x00FFFFFF);

        let mut st = STATE.lock().unwrap();
        let maximized = st.restore_rect.is_some();

        // ① 상단 메뉴바
        fill(RECT { left: 0, top: 0, right: w, bottom: head }, HEAD_BG);
        for b in HEAD_BUTTONS {
            let (l, r) = head_button_span(b, w, bw);
            let br = RECT { left: l, top: 0, right: r, bottom: head };
            let hovered = st.hover_btn == Some(b);
            let on = b == HeadButton::Pin && pinned;
            if hovered {
                fill(br, if b == HeadButton::Close { 0x002311E8 } else if st.pressed_btn == Some(b) { 0x00CFC6BC } else { 0x00E0D8CF });
            } else if on {
                fill(br, 0x00F2DCC4);
            }
            SetTextColor(mem, if hovered && b == HeadButton::Close { 0x00FFFFFF } else if on { ACCENT } else { 0x00333333 });
            SelectObject(mem, if matches!(b, HeadButton::Capture | HeadButton::Pin) { glyph_big } else { glyph });
            draw(&head_button_glyph(b, pinned, maximized).to_string(), br, DT_CENTER);
        }
        let buttons_left = head_button_span(HEAD_BUTTONS[0], w, bw).0;
        SelectObject(mem, title_font);
        SetTextColor(mem, 0x00222222);
        let title_left = scale(hwnd, 10);
        draw("몽땅클립보드", RECT { left: title_left, top: 0, right: buttons_left - scale(hwnd, 4), bottom: head }, DT_END_ELLIPSIS);
        let title_right = title_left + text_width(mem, "몽땅클립보드") + scale(hwnd, 8);
        if title_right < buttons_left - scale(hwnd, 24) {
            SelectObject(mem, small);
            SetTextColor(mem, 0x00777777);
            let hint = match st.hover_btn {
                Some(b) => head_button_name(b, pinned, maximized).to_string(),
                None => "1~9 선택 · ←→ 분류".to_string(),
            };
            draw(&hint, RECT { left: title_right, top: 0, right: buttons_left - scale(hwnd, 4), bottom: head }, DT_END_ELLIPSIS);
        }

        // 접힘 여부는 설정값이 아니라 실제 창 높이로 판단한다(설정값과 창 높이가 어긋나도 목록이 가려지지 않게).
        let collapsed = h < head + cat_h + row;
        if collapsed {
            st.tab_spans.clear();
            drop(st);
            BitBlt(hdc, 0, 0, w, h, mem, 0, 0, SRCCOPY);
            return;
        }

        // ② 분류 메뉴바
        fill(RECT { left: 0, top: head, right: w, bottom: head + cat_h }, 0x00FAFAFA);
        fill(RECT { left: 0, top: head + cat_h - 1, right: w, bottom: head + cat_h }, 0x00E3E3E3);
        SelectObject(mem, small_bold);
        let long: Vec<i32> = TABS.iter().map(|t| text_width(mem, t.label(false))).collect();
        let short: Vec<i32> = TABS.iter().map(|t| text_width(mem, t.label(true))).collect();
        let margin = scale(hwnd, TAB_MARGIN);
        let (spans, use_short) = tab_layout(&long, &short, w - 2 * margin, scale(hwnd, TAB_PAD), scale(hwnd, TAB_MIN_PAD));
        st.tab_spans = spans.iter().map(|(l, r)| (l + margin, r + margin)).collect();
        for (i, tab) in TABS.iter().enumerate() {
            let (l, r) = st.tab_spans[i];
            let tr = RECT { left: l, top: head, right: r, bottom: head + cat_h - 1 };
            let selected = i == st.tab;
            if selected {
                fill(tr, 0x00FFFFFF);
                fill(RECT { left: l + scale(hwnd, 3), top: head + cat_h - scale(hwnd, 3), right: r - scale(hwnd, 3),
                            bottom: head + cat_h - 1 }, ACCENT);
                SelectObject(mem, small_bold);
                SetTextColor(mem, ACCENT);
            } else {
                if st.hover_tab == Some(i) {
                    fill(tr, 0x00EFEFEF);
                }
                SelectObject(mem, small);
                SetTextColor(mem, 0x00444444);
            }
            draw(tab.label(use_short), tr, DT_CENTER | DT_END_ELLIPSIS);
        }

        // 키워드검색 입력 줄
        let tab = st.current();
        let searching = tab == Tab::Search;
        let needle = st.needle();
        if searching {
            let y = head + cat_h;
            let pad = scale(hwnd, 6);
            let boxr = RECT { left: pad, top: y + scale(hwnd, 3), right: w - pad, bottom: y + row - scale(hwnd, 3) };
            let border = CreateSolidBrush(ACCENT);
            if !border.is_null() {
                FrameRect(mem, &boxr, border);
                DeleteObject(border);
            }
            SelectObject(mem, small);
            let text_r = RECT { left: boxr.left + pad, top: boxr.top, right: boxr.right - pad, bottom: boxr.bottom };
            if needle.is_empty() {
                SetTextColor(mem, 0x00888888);
                draw("▏찾을 글자를 입력하세요 · 저장된 모든 항목에서 찾기", text_r, DT_END_ELLIPSIS);
            } else {
                SetTextColor(mem, 0x00222222);
                draw(&format!("{}{}▏  · {}개 · Esc 지우기", st.query, st.comp, st.items.len()), text_r, DT_END_ELLIPSIS);
            }
        }

        // ③ 목록
        let top_y = list_top(head, cat_h, searching, row);
        let visible_rows = ((h - top_y).max(0) / row).max(1) as usize;
        if st.items.is_empty() {
            SelectObject(mem, font);
            SetTextColor(mem, 0x00666666);
            let msg = match tab {
                Tab::Search if !needle.trim().is_empty() => "찾는 글자가 들어 있는 항목이 없습니다.".to_string(),
                Tab::Cat(Category::All) | Tab::Search => "아직 기록된 항목이 없습니다. 무엇이든 복사해 보세요.".to_string(),
                Tab::Cat(c) => format!("'{}' 분류에 해당하는 항목이 없습니다.", c.label()),
            };
            draw(&msg, RECT { left: scale(hwnd, 12), top: top_y, right: w, bottom: top_y + row }, DT_END_ELLIPSIS);
        }
        for (i, item) in st.items.iter().enumerate().skip(st.top).take(visible_rows) {
            let y = top_y + (i - st.top) as i32 * row;
            let r = RECT { left: 0, top: y, right: w, bottom: y + row };
            if i == st.sel {
                fill(r, 0x00F7E3CF);
            } else if st.hover == Some(i) {
                fill(r, 0x00FBF3EC);
            }
            SelectObject(mem, small);
            SetTextColor(mem, 0x00EB6325);
            let shortcut = if i - st.top < 9 && needle.is_empty() { format!("{}", i - st.top + 1) } else { String::new() };
            draw(&shortcut, RECT { left: scale(hwnd, 8), top: y, right: scale(hwnd, 24), bottom: y + row }, DT_CENTER);
            SetTextColor(mem, 0x00888888);
            let tag = format!("{}{}{}{}", if item.pinned { "★" } else { "" }, kind_tag(&item.kind),
                if item.preview.contains("웹 ·") { " · 웹" } else { "" },
                if item.preview.contains("서식 포함") { " · 서식 포함" } else { "" });
            draw(&tag, RECT { left: scale(hwnd, 28), top: y, right: scale(hwnd, 70), bottom: y + row }, 0);
            SelectObject(mem, font);
            SetTextColor(mem, 0x00222222);
            let actions = if st.hover == Some(i) { scale(hwnd, ROW_PIN_W + ROW_DELETE_W) } else { 0 };
            draw(&item.preview, RECT { left: scale(hwnd, 72), top: y, right: w - actions - scale(hwnd, 10), bottom: y + row },
                 DT_END_ELLIPSIS);
            if st.hover == Some(i) {
                let del = RECT { left: w - scale(hwnd, ROW_DELETE_W), top: y, right: w, bottom: y + row };
                let pin = RECT { left: del.left - scale(hwnd, ROW_PIN_W), top: y, right: del.left, bottom: y + row };
                SetTextColor(mem, 0x00555555);
                draw("✕", del, DT_CENTER);
                draw(if item.pinned { "📌" } else { "📍" }, pin, DT_CENTER);
            }
        }
        drop(st);
        BitBlt(hdc, 0, 0, w, h, mem, 0, 0, SRCCOPY);
    }
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

fn xy(lp: LPARAM) -> (i32, i32) {
    ((lp & 0xFFFF) as i16 as i32, ((lp >> 16) & 0xFFFF) as i16 as i32)
}

fn client_width(hwnd: HWND) -> i32 {
    let mut rc: RECT = unsafe { std::mem::zeroed() };
    unsafe { GetClientRect(hwnd, &mut rc) };
    rc.right
}

fn head_button_at(hwnd: HWND, x: i32, y: i32) -> Option<HeadButton> {
    head_button(x, y, client_width(hwnd), scale(hwnd, CAPTION_W), scale(hwnd, HEAD_H))
}

/// 분류 메뉴바 위의 단추 위치.
fn tab_hit(hwnd: HWND, x: i32, y: i32) -> Option<usize> {
    let head = scale(hwnd, HEAD_H);
    if y < head || y >= head + scale(hwnd, CAT_H) {
        return None;
    }
    tab_at(x, &STATE.lock().unwrap().tab_spans)
}

fn row_at(hwnd: HWND, lp: LPARAM) -> Option<usize> {
    let (_, y) = xy(lp);
    let st = STATE.lock().unwrap();
    let top_y = list_top(scale(hwnd, HEAD_H), scale(hwnd, CAT_H), st.current() == Tab::Search, scale(hwnd, ROW_H));
    row_index(y, top_y, scale(hwnd, ROW_H), st.top, st.items.len())
}

/// 머리글·빈 곳 오른쪽 클릭 메뉴 항목(접기·모두 지우기). 항목 메뉴 뒤에도 붙인다.
unsafe fn append_window_items(menu: HMENU, separator: bool) {
    unsafe {
        let collapsed = app().settings.lock().unwrap().popup_collapsed;
        if separator {
            AppendMenuW(menu, MF_SEPARATOR, 0, std::ptr::null());
        }
        AppendMenuW(menu, MF_STRING, CMD_COLLAPSE, wide(if collapsed { "목록 펼치기" } else { "목록 접기" }).as_ptr());
        AppendMenuW(menu, MF_STRING, CMD_CLEAR, wide("모두 지우기(고정 항목 제외)…").as_ptr());
    }
}

fn run_window_command(hwnd: HWND, command: usize) -> bool {
    match command {
        CMD_COLLAPSE => { toggle_collapse(hwnd); true }
        CMD_CLEAR => { clear_all(hwnd); true }
        _ => false,
    }
}

unsafe fn window_menu(hwnd: HWND, pt: POINT) {
    unsafe {
        let menu = CreatePopupMenu();
        if menu.is_null() {
            return;
        }
        append_window_items(menu, false);
        let command = TrackPopupMenu(menu, TPM_RETURNCMD | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, std::ptr::null());
        DestroyMenu(menu);
        run_window_command(hwnd, command as usize);
    }
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
                // 사용자가 끌어 옮기거나 크기를 바꾸면 최대화 상태는 끝난다.
                STATE.lock().unwrap().restore_rect = None;
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
                InvalidateRect(hwnd, std::ptr::null(), 0);
                0
            }
            WM_ACTIVATE if (wp & 0xFFFF) as u32 == WA_INACTIVE => {
                if !app().settings.lock().unwrap().sticky_popup { hide(); }
                0
            }
            WM_MOUSEACTIVATE => {
                // 상단 메뉴바 단추는 눌러도 창을 활성화하지 않는다(붙여넣을 창의 포커스 유지).
                let mut pt = POINT { x: 0, y: 0 };
                GetCursorPos(&mut pt);
                ScreenToClient(hwnd, &mut pt);
                if head_button_at(hwnd, pt.x, pt.y).is_some() {
                    return MA_NOACTIVATE as LRESULT;
                }
                DefWindowProcW(hwnd, msg, wp, lp)
            }
            WM_NCHITTEST => {
                let hit = DefWindowProcW(hwnd, msg, wp, lp);
                if hit != HTCLIENT as LRESULT {
                    return hit; // 틀(크기 조절)
                }
                let (sx, sy) = xy(lp);
                let mut pt = POINT { x: sx, y: sy };
                ScreenToClient(hwnd, &mut pt);
                if pt.y >= 0 && pt.y < scale(hwnd, HEAD_H) && head_button_at(hwnd, pt.x, pt.y).is_none() {
                    HTCAPTION as LRESULT
                } else {
                    HTCLIENT as LRESULT
                }
            }
            WM_NCLBUTTONDBLCLK if wp == HTCAPTION as usize => {
                toggle_max(hwnd);
                0
            }
            WM_NCRBUTTONUP if wp == HTCAPTION as usize => {
                let (x, y) = xy(lp);
                window_menu(hwnd, POINT { x, y });
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
                            refilter(false);
                        } else {
                            hide();
                        }
                    }
                    VK_BACK => {
                        let changed = STATE.lock().unwrap().query.pop().is_some();
                        if changed {
                            refilter(false);
                        }
                    }
                    VK_LEFT | VK_RIGHT | VK_TAB => {
                        let back = vk == VK_LEFT || (vk == VK_TAB && GetKeyState(VK_SHIFT as i32) < 0);
                        let cur = STATE.lock().unwrap().tab;
                        set_tab(next_tab(cur, if back { -1 } else { 1 }));
                    }
                    0x46 if GetKeyState(VK_CONTROL as i32) < 0 => set_tab(SEARCH_TAB), // Ctrl+F
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
                // 어느 분류에서든 글자를 치면 키워드검색(모든 항목 대상)으로 넘어간다.
                st.tab = SEARCH_TAB;
                st.query.push(ch);
                st.comp.clear();
                drop(st);
                refilter(false);
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
                    {
                        let mut st = STATE.lock().unwrap();
                        st.comp = String::from_utf16_lossy(&buf);
                        if !st.comp.is_empty() {
                            st.tab = SEARCH_TAB;
                        }
                    }
                    refilter(false);
                }
                // 확정 글자는 기본 처리가 WM_CHAR로 보낸다.
                DefWindowProcW(hwnd, msg, wp, lp)
            }
            WM_IME_ENDCOMPOSITION => {
                STATE.lock().unwrap().comp.clear();
                DefWindowProcW(hwnd, msg, wp, lp)
            }
            WM_MOUSEMOVE => {
                if !TRACKING.swap(true, Ordering::Relaxed) {
                    let mut tme = TRACKMOUSEEVENT {
                        cbSize: std::mem::size_of::<TRACKMOUSEEVENT>() as u32, dwFlags: TME_LEAVE, hwndTrack: hwnd,
                        dwHoverTime: 0,
                    };
                    TrackMouseEvent(&mut tme);
                }
                let (x, y) = xy(lp);
                let btn = head_button_at(hwnd, x, y);
                let tab = tab_hit(hwnd, x, y);
                let i = row_at(hwnd, lp);
                let mut st = STATE.lock().unwrap();
                if st.hover != i || st.hover_btn != btn || st.hover_tab != tab {
                    st.hover = i;
                    st.hover_btn = btn;
                    st.hover_tab = tab;
                    drop(st);
                    InvalidateRect(hwnd, std::ptr::null(), 0);
                }
                0
            }
            WM_MOUSELEAVE => {
                TRACKING.store(false, Ordering::Relaxed);
                let mut st = STATE.lock().unwrap();
                st.hover = None;
                st.hover_btn = None;
                st.hover_tab = None;
                st.pressed_btn = None;
                drop(st);
                InvalidateRect(hwnd, std::ptr::null(), 0);
                0
            }
            WM_LBUTTONDOWN => {
                let (x, y) = xy(lp);
                let btn = head_button_at(hwnd, x, y);
                STATE.lock().unwrap().pressed_btn = btn;
                if btn.is_some() {
                    InvalidateRect(hwnd, std::ptr::null(), 0);
                }
                0
            }
            WM_LBUTTONUP => {
                let (x, y) = xy(lp);
                let pressed = STATE.lock().unwrap().pressed_btn.take();
                let btn = head_button_at(hwnd, x, y);
                if btn.is_some() || pressed.is_some() {
                    // Windows 캡션 단추처럼 누른 단추 위에서 뗄 때만 동작한다.
                    match btn.filter(|b| Some(*b) == pressed) {
                        Some(HeadButton::Capture) => { hide(); crate::capture_screen(); }
                        Some(HeadButton::Pin) => toggle_pin(),
                        Some(HeadButton::Minimize) => minimize(),
                        Some(HeadButton::Maximize) => toggle_max(hwnd),
                        Some(HeadButton::Close) => hide(),
                        None => {}
                    }
                    InvalidateRect(hwnd, std::ptr::null(), 0);
                    return 0;
                }
                if let Some(t) = tab_hit(hwnd, x, y) {
                    set_tab(t);
                    InvalidateRect(hwnd, std::ptr::null(), 0);
                    return 0;
                }
                if let Some(i) = row_at(hwnd, lp) {
                    let w = client_width(hwnd);
                    let action_width = scale(hwnd, ROW_PIN_W + ROW_DELETE_W);
                    if STATE.lock().unwrap().hover == Some(i) && x >= w - action_width {
                        let item = { let st = STATE.lock().unwrap(); st.items.get(i).map(|v| (v.id, v.pinned)) };
                        if let Some((id, pinned)) = item {
                            if row_action(x, w, scale(hwnd, ROW_PIN_W), scale(hwnd, ROW_DELETE_W)) == Some(true) {
                                let _ = app().store.lock().unwrap().pin(id, !pinned);
                            } else {
                                let _ = app().store.lock().unwrap().delete(id);
                            }
                        }
                        refresh_recent();
                        refresh();
                        return 0;
                    }
                    choose(i);
                }
                0
            }
            WM_RBUTTONUP => {
                let (cx, cy) = xy(lp);
                let mut pt = POINT { x: cx, y: cy };
                ClientToScreen(hwnd, &mut pt);
                let item = row_at(hwnd, lp).and_then(|i| {
                    let st = STATE.lock().unwrap();
                    st.items.get(i).map(|v| (v.id, v.kind.clone(), v.preview.contains("웹 ·")))
                });
                let Some((id, kind, web)) = item else {
                    window_menu(hwnd, pt);
                    return 0;
                };
                let menu = CreatePopupMenu();
                if menu.is_null() {
                    return 0;
                }
                AppendMenuW(menu, MF_STRING, 1, wide("열기").as_ptr());
                if web {
                    if kind == "text" { AppendMenuW(menu, MF_STRING, 3, wide("글을 연결 프로그램으로 열기").as_ptr()); }
                } else {
                    AppendMenuW(menu, MF_STRING, 2, wide("연결 프로그램 선택…").as_ptr());
                }
                append_window_items(menu, true);
                let command = TrackPopupMenu(menu, TPM_RETURNCMD | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, std::ptr::null());
                DestroyMenu(menu);
                if run_window_command(hwnd, command as usize) {
                    return 0;
                }
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
mod tests {
    use super::*;
    use crate::category::CategorySet;

    #[test]
    fn caption_buttons_right_to_left_close_max_min_pin_capture() {
        // 폭 600, 단추 46: 닫기 554..600, 최대화 508..554, 최소화 462..508, 항상 위 416..462, 캡처 370..416
        assert_eq!(head_button(599, 5, 600, 46, 32), Some(HeadButton::Close));
        assert_eq!(head_button(554, 5, 600, 46, 32), Some(HeadButton::Close));
        assert_eq!(head_button(553, 5, 600, 46, 32), Some(HeadButton::Maximize));
        assert_eq!(head_button(508, 5, 600, 46, 32), Some(HeadButton::Maximize));
        assert_eq!(head_button(507, 5, 600, 46, 32), Some(HeadButton::Minimize));
        assert_eq!(head_button(462, 5, 600, 46, 32), Some(HeadButton::Minimize));
        assert_eq!(head_button(461, 5, 600, 46, 32), Some(HeadButton::Pin));
        assert_eq!(head_button(416, 5, 600, 46, 32), Some(HeadButton::Pin));
        assert_eq!(head_button(415, 5, 600, 46, 32), Some(HeadButton::Capture));
        assert_eq!(head_button(370, 5, 600, 46, 32), Some(HeadButton::Capture));
        assert_eq!(head_button(369, 5, 600, 46, 32), None); // 제목(끌어 옮기기) 영역
        assert_eq!(head_button(10, 5, 600, 46, 32), None);
    }

    #[test]
    fn caption_buttons_only_in_header_and_inside_window() {
        assert_eq!(head_button(599, 32, 600, 46, 32), None);
        assert_eq!(head_button(599, -1, 600, 46, 32), None);
        assert_eq!(head_button(600, 5, 600, 46, 32), None);
        assert_eq!(head_button(-1, 5, 600, 46, 32), None);
    }

    #[test]
    fn caption_button_spans_are_equal_and_contiguous() {
        let spans: Vec<_> = HEAD_BUTTONS.iter().map(|b| head_button_span(*b, 320, 46)).collect();
        assert_eq!(spans.last().unwrap().1, 320);
        assert_eq!(spans[0].0, 320 - 46 * 5); // 최소 폭에서도 제목 칸 90px 남음
        for pair in spans.windows(2) {
            assert_eq!(pair[0].1, pair[1].0);
        }
        assert!(spans.iter().all(|(l, r)| r - l == 46));
    }

    #[test]
    fn caption_glyphs_and_names_reflect_state() {
        assert_eq!(head_button_glyph(HeadButton::Maximize, false, false), '\u{E922}');
        assert_eq!(head_button_glyph(HeadButton::Maximize, false, true), '\u{E923}');
        assert_eq!(head_button_glyph(HeadButton::Pin, true, false), '\u{E840}');
        assert_eq!(head_button_glyph(HeadButton::Pin, false, false), '\u{E718}');
        assert_eq!(head_button_name(HeadButton::Pin, true, false), "항상 위 끄기 (켜짐)");
        assert_eq!(head_button_name(HeadButton::Maximize, false, true), "이전 크기로 복원");
    }

    #[test]
    fn tabs_order_labels_and_default() {
        let labels: Vec<_> = TABS.iter().map(|t| t.label(false)).collect();
        assert_eq!(labels, ["전체", "문서", "그림", "파일", "폴더", "웹", "화면캡처", "키워드검색"]);
        assert_eq!(TABS[0], Tab::Cat(Category::All));
        assert_eq!(TABS[SEARCH_TAB], Tab::Search);
        assert_eq!(Tab::Search.label(true), "검색");
        assert_eq!(Tab::Cat(Category::Capture).label(true), "캡처");
    }

    #[test]
    fn tab_navigation_wraps() {
        assert_eq!(next_tab(0, 1), 1);
        assert_eq!(next_tab(0, -1), SEARCH_TAB);
        assert_eq!(next_tab(SEARCH_TAB, 1), 0);
    }

    fn assert_fits(spans: &[(i32, i32)], avail: i32) {
        assert!(spans.first().unwrap().0 >= 0 && spans.last().unwrap().1 <= avail);
        for pair in spans.windows(2) {
            assert!(pair[0].1 <= pair[1].0, "겹침: {pair:?}");
        }
    }

    #[test]
    fn tab_layout_shrinks_padding_then_short_labels_then_equal_share() {
        let long = [24, 24, 24, 24, 24, 12, 48, 60];
        let short = [24, 24, 24, 24, 24, 12, 24, 24];
        // 넉넉하면 기본 여백 9
        let (s, short_used) = tab_layout(&long, &short, 600, 9, 4);
        assert!(!short_used);
        assert_eq!(s[0], (0, 42));
        assert_eq!(s[7].1, 240 + 8 * 18);
        assert_fits(&s, 600);
        // 기본 여백이 넘치면 최소 여백 4 (240 + 64 = 304)
        let (s, short_used) = tab_layout(&long, &short, 320, 9, 4);
        assert!(!short_used);
        assert_eq!(s[7].1, 304);
        assert_fits(&s, 320);
        // 그래도 넘치면 짧은 이름 (180 + 64 = 244)
        let (s, short_used) = tab_layout(&long, &short, 260, 9, 4);
        assert!(short_used);
        assert_eq!(s[7].1, 244);
        // 마지막: 같은 폭으로 나눔(말줄임)
        let (s, short_used) = tab_layout(&long, &short, 200, 9, 4);
        assert!(short_used);
        assert_eq!(s.len(), 8);
        assert_eq!((s[0], s[7].1), ((0, 25), 200));
        assert_fits(&s, 200);
        let (s, _) = tab_layout(&long, &short, -5, 9, 4);
        assert!(s.iter().all(|(l, r)| *l == 0 && *r == 0));
    }

    #[test]
    fn tab_hit_uses_spans() {
        let spans = [(6, 48), (48, 90), (90, 132)];
        assert_eq!(tab_at(5, &spans), None);
        assert_eq!(tab_at(6, &spans), Some(0));
        assert_eq!(tab_at(48, &spans), Some(1));
        assert_eq!(tab_at(131, &spans), Some(2));
        assert_eq!(tab_at(132, &spans), None);
    }

    #[test]
    fn list_rows_start_below_category_bar_and_search_row() {
        assert_eq!(list_top(32, 28, false, 30), 60);
        assert_eq!(list_top(32, 28, true, 30), 90);
        assert_eq!(row_index(59, 60, 30, 0, 5), None);
        assert_eq!(row_index(60, 60, 30, 0, 5), Some(0));
        assert_eq!(row_index(119, 60, 30, 0, 5), Some(1));
        assert_eq!(row_index(120, 60, 30, 3, 5), None); // 스크롤 3 + 2 = 5 → 목록 밖
        assert_eq!(row_index(90, 60, 30, 3, 5), Some(4));
    }

    #[test]
    fn hover_actions_reserve_right_side_only() {
        assert_eq!(row_action(543, 600, 28, 28), None);
        assert_eq!(row_action(544, 600, 28, 28), Some(true));
        assert_eq!(row_action(572, 600, 28, 28), Some(false));
        assert_eq!(row_action(600, 600, 28, 28), None);
    }

    fn item(id: i64, pinned: bool, cats: &[Category]) -> Summary {
        Summary { id, kind: "text".into(), preview: format!("{id}"), pinned, used: 0.0, size: 0,
                  cats: CategorySet::of(&[&[Category::All][..], cats].concat()) }
    }

    #[test]
    fn memory_filter_keeps_newest_first_and_pinned_on_top() {
        // 저장소 순서 = 최근 사용 순(5가 가장 최근)
        let v = vec![item(5, false, &[Category::Web]), item(4, true, &[]), item(3, false, &[Category::Document]),
                     item(2, false, &[Category::Web, Category::Document]), item(1, true, &[Category::Web])];
        let ids = |v: Vec<Summary>| v.iter().map(|x| x.id).collect::<Vec<_>>();
        assert_eq!(ids(order_items(filter_memory(&v, Tab::Cat(Category::All)))), vec![4, 1, 5, 3, 2]);
        assert_eq!(ids(order_items(filter_memory(&v, Tab::Cat(Category::Web)))), vec![1, 5, 2]);
        assert_eq!(ids(order_items(filter_memory(&v, Tab::Cat(Category::Document)))), vec![3, 2]);
        assert!(filter_memory(&v, Tab::Cat(Category::Capture)).is_empty());
        assert_eq!(filter_memory(&v, Tab::Search).len(), 5);
    }

    #[test]
    fn store_is_consulted_only_when_memory_may_be_incomplete() {
        let full = crate::RECENT;
        assert!(!needs_store(Tab::Cat(Category::All), full, full, true));
        assert!(!needs_store(Tab::Cat(Category::Web), 10, 3, true)); // 기록 전체가 메모리에 있음
        assert!(needs_store(Tab::Cat(Category::Web), full, 3, true)); // 더 오래된 웹 항목이 있을 수 있음
        assert!(!needs_store(Tab::Cat(Category::Web), full, LIST_LIMIT, true));
        assert!(!needs_store(Tab::Search, full, full, true)); // 빈 찾기 = 메모리 목록
        assert!(needs_store(Tab::Search, 3, 0, false)); // 찾기는 모든 항목 대상
    }
}
