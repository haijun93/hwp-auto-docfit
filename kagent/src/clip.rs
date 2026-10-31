//! 클립보드 읽기·쓰기. 클립보드는 짧게만 열고(복사해 두고 바로 닫음) 무거운 일은 작업 스레드가 한다.

use std::sync::OnceLock;

use windows_sys::Win32::Foundation::{CloseHandle, HANDLE, HWND};
use windows_sys::Win32::System::DataExchange::{
    CloseClipboard, EmptyClipboard, GetClipboardData, GetClipboardOwner, IsClipboardFormatAvailable, OpenClipboard,
    RegisterClipboardFormatW, SetClipboardData,
};
use windows_sys::Win32::Foundation::GlobalFree;
use windows_sys::Win32::System::Memory::{GMEM_MOVEABLE, GlobalAlloc, GlobalLock, GlobalSize, GlobalUnlock};
use windows_sys::Win32::System::Ole::{CF_DIB, CF_HDROP, CF_UNICODETEXT};
use windows_sys::Win32::System::Threading::{
    OpenProcess, PROCESS_NAME_WIN32, PROCESS_QUERY_LIMITED_INFORMATION, QueryFullProcessImageNameW,
};
use windows_sys::Win32::UI::Shell::{DROPFILES, DragQueryFileW, HDROP};
use windows_sys::Win32::UI::WindowsAndMessaging::{GetForegroundWindow, GetWindowThreadProcessId};

use crate::util::wide;

pub enum Capture {
    /// 글과 같은 내용의 서식 형식 묶음(HTML·RTF, pack_formats).
    Text(String, Vec<u8>),
    Files(Vec<String>),
    Png(Vec<u8>),
    Dib(Vec<u8>),
}

/// 글과 함께 보관해 되돌릴 서식 형식(이름으로 등록되는 형식).
const RICH_FORMATS: [&str; 2] = ["HTML Format", "Rich Text Format"];

struct Formats {
    rich: [u32; 2],
    png: u32,
    exclude: u32,
    history: u32,
}

fn formats() -> &'static Formats {
    static F: OnceLock<Formats> = OnceLock::new();
    F.get_or_init(|| unsafe {
        Formats {
            rich: RICH_FORMATS.map(|name| RegisterClipboardFormatW(wide(name).as_ptr())),
            png: RegisterClipboardFormatW(wide("PNG").as_ptr()),
            exclude: RegisterClipboardFormatW(wide("ExcludeClipboardContentFromMonitorProcessing").as_ptr()),
            history: RegisterClipboardFormatW(wide("CanIncludeInClipboardHistory").as_ptr()),
        }
    })
}

struct Open;

impl Open {
    fn new(hwnd: HWND) -> Option<Open> {
        // 다른 프로그램이 잠깐 열고 있을 수 있어 몇 번만 다시 시도한다.
        for _ in 0..5 {
            if unsafe { OpenClipboard(hwnd) } != 0 {
                return Some(Open);
            }
            std::thread::sleep(std::time::Duration::from_millis(4));
        }
        None
    }
}

impl Drop for Open {
    fn drop(&mut self) {
        unsafe { CloseClipboard() };
    }
}

unsafe fn global_bytes(h: HANDLE, max: usize) -> Option<Vec<u8>> {
    if h.is_null() {
        return None;
    }
    let size = unsafe { GlobalSize(h) };
    if size == 0 || size > max {
        return None;
    }
    let p = unsafe { GlobalLock(h) } as *const u8;
    if p.is_null() {
        return None;
    }
    let v = unsafe { std::slice::from_raw_parts(p, size) }.to_vec();
    unsafe { GlobalUnlock(h) };
    Some(v)
}

/// 클립보드 주인(없으면 앞 창)의 실행 파일 이름(소문자).
pub fn source_app() -> String {
    unsafe {
        let mut hwnd = GetClipboardOwner();
        if hwnd.is_null() {
            hwnd = GetForegroundWindow();
        }
        let mut pid = 0u32;
        GetWindowThreadProcessId(hwnd, &mut pid);
        if pid == 0 {
            return String::new();
        }
        let process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid);
        if process.is_null() {
            return String::new();
        }
        let mut buf = [0u16; 1024];
        let mut len = buf.len() as u32;
        let ok = QueryFullProcessImageNameW(process, PROCESS_NAME_WIN32, buf.as_mut_ptr(), &mut len);
        CloseHandle(process);
        if ok == 0 {
            return String::new();
        }
        let path = String::from_utf16_lossy(&buf[..len as usize]);
        path.rsplit('\\').next().unwrap_or("").to_lowercase()
    }
}

/// 지금 클립보드를 읽는다. 기록하면 안 되는 내용(제외 신호)이면 None.
/// 우선순위: 파일 > 텍스트 > PNG > 비트맵.
pub fn read(hwnd: HWND, max_bytes: usize) -> Option<Capture> {
    let f = formats();
    let _open = Open::new(hwnd)?;
    unsafe {
        if IsClipboardFormatAvailable(f.exclude) != 0 {
            return None;
        }
        if IsClipboardFormatAvailable(f.history) != 0 {
            if let Some(b) = global_bytes(GetClipboardData(f.history), 16) {
                if b.len() >= 4 && u32::from_le_bytes([b[0], b[1], b[2], b[3]]) == 0 {
                    return None;
                }
            }
        }
        if IsClipboardFormatAvailable(CF_HDROP as u32) != 0 {
            let h = GetClipboardData(CF_HDROP as u32) as HDROP;
            if !h.is_null() {
                let count = DragQueryFileW(h, u32::MAX, std::ptr::null_mut(), 0).min(10000);
                let mut files = Vec::with_capacity(count as usize);
                let mut buf = vec![0u16; 32768];
                for i in 0..count {
                    let n = DragQueryFileW(h, i, buf.as_mut_ptr(), buf.len() as u32) as usize;
                    if n > 0 {
                        files.push(String::from_utf16_lossy(&buf[..n]));
                    }
                }
                if !files.is_empty() {
                    return Some(Capture::Files(files));
                }
            }
        }
        if IsClipboardFormatAvailable(CF_UNICODETEXT as u32) != 0 {
            if let Some(b) = global_bytes(GetClipboardData(CF_UNICODETEXT as u32), max_bytes) {
                let units: Vec<u16> = b.chunks_exact(2).map(|c| u16::from_le_bytes([c[0], c[1]])).collect();
                let end = units.iter().position(|&u| u == 0).unwrap_or(units.len());
                let text = String::from_utf16_lossy(&units[..end]);
                if !text.trim().is_empty() {
                    let mut rich = Vec::new();
                    for (name, fmt) in RICH_FORMATS.iter().zip(f.rich) {
                        if fmt != 0 && IsClipboardFormatAvailable(fmt) != 0 {
                            if let Some(bytes) = global_bytes(GetClipboardData(fmt), max_bytes) {
                                rich.push((name.to_string(), bytes));
                            }
                        }
                    }
                    return Some(Capture::Text(text, pack_formats(&rich)));
                }
            }
        }
        if f.png != 0 && IsClipboardFormatAvailable(f.png) != 0 {
            if let Some(b) = global_bytes(GetClipboardData(f.png), max_bytes) {
                if b.starts_with(b"\x89PNG") {
                    return Some(Capture::Png(b));
                }
            }
        }
        if IsClipboardFormatAvailable(CF_DIB as u32) != 0 {
            // 비트맵은 PNG로 줄이기 전이라 상한을 넉넉히(4배) 둔다.
            if let Some(b) = global_bytes(GetClipboardData(CF_DIB as u32), max_bytes.saturating_mul(4)) {
                return Some(Capture::Dib(b));
            }
        }
    }
    None
}

unsafe fn put(format: u32, data: &[u8]) -> bool {
    unsafe {
        let h = GlobalAlloc(GMEM_MOVEABLE, data.len().max(1));
        if h.is_null() {
            return false;
        }
        let p = GlobalLock(h) as *mut u8;
        if p.is_null() {
            GlobalFree(h);
            return false;
        }
        std::ptr::copy_nonoverlapping(data.as_ptr(), p, data.len());
        GlobalUnlock(h);
        if SetClipboardData(format, h).is_null() {
            GlobalFree(h);
            return false;
        }
        true
    }
}

/// [개수][이름 길이·이름·자료 길이·자료]… (작은 끝 u32). 비어 있으면 빈 바이트.
pub fn pack_formats(formats: &[(String, Vec<u8>)]) -> Vec<u8> {
    if formats.is_empty() {
        return Vec::new();
    }
    let mut out = (formats.len() as u32).to_le_bytes().to_vec();
    for (name, data) in formats {
        out.extend_from_slice(&(name.len() as u32).to_le_bytes());
        out.extend_from_slice(name.as_bytes());
        out.extend_from_slice(&(data.len() as u32).to_le_bytes());
        out.extend_from_slice(data);
    }
    out
}

pub fn unpack_formats(mut data: &[u8]) -> Vec<(String, Vec<u8>)> {
    let mut take = |n: usize| -> Option<&[u8]> {
        let (head, rest) = (data.get(..n)?, data.get(n..)?);
        data = rest;
        Some(head)
    };
    let mut out = Vec::new();
    let Some(count) = take(4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]])) else { return out };
    for _ in 0..count.min(16) {
        let Some(len) = take(4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as usize) else { break };
        let Some(name) = take(len).map(|b| String::from_utf8_lossy(b).into_owned()) else { break };
        let Some(len) = take(4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as usize) else { break };
        let Some(bytes) = take(len) else { break };
        out.push((name, bytes.to_vec()));
    }
    out
}

/// 저장한 항목을 원래 형식으로 클립보드에 올린다(글은 함께 보관한 HTML·RTF도).
pub fn write(hwnd: HWND, kind: &str, payload: &[u8], extra: &[u8]) -> bool {
    let Some(_open) = Open::new(hwnd) else { return false };
    unsafe {
        if EmptyClipboard() == 0 {
            return false;
        }
        match kind {
            "text" => {
                let mut units: Vec<u16> = String::from_utf8_lossy(payload).encode_utf16().collect();
                units.push(0);
                let bytes: Vec<u8> = units.iter().flat_map(|u| u.to_le_bytes()).collect();
                let ok = put(CF_UNICODETEXT as u32, &bytes);
                for (name, data) in unpack_formats(extra) {
                    if let Some(i) = RICH_FORMATS.iter().position(|n| *n == name) {
                        put(formats().rich[i], &data);
                    }
                }
                ok
            }
            "files" => {
                let text = String::from_utf8_lossy(payload);
                let mut data = Vec::new();
                let header = DROPFILES {
                    pFiles: std::mem::size_of::<DROPFILES>() as u32,
                    pt: windows_sys::Win32::Foundation::POINT { x: 0, y: 0 },
                    fNC: 0,
                    fWide: 1,
                };
                data.extend_from_slice(std::slice::from_raw_parts(
                    &header as *const DROPFILES as *const u8, std::mem::size_of::<DROPFILES>()));
                for path in text.split('\n').filter(|p| !p.is_empty()) {
                    for u in path.encode_utf16().chain([0]) {
                        data.extend_from_slice(&u.to_le_bytes());
                    }
                }
                data.extend_from_slice(&[0, 0]);
                put(CF_HDROP as u32, &data)
            }
            "image" => {
                let png_ok = put(formats().png, payload);
                let dib_ok = png_to_dib(payload).map(|d| put(CF_DIB as u32, &d)).unwrap_or(false);
                png_ok || dib_ok
            }
            _ => false,
        }
    }
}

/// CF_DIB(24·32비트, BI_RGB·BI_BITFIELDS) → PNG. 다른 형식은 None(기록하지 않음).
pub fn dib_to_png(dib: &[u8]) -> Option<Vec<u8>> {
    let u32_at = |o: usize| dib.get(o..o + 4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]));
    let header = u32_at(0)? as usize;
    let width = u32_at(4)? as i32;
    let height = u32_at(8)? as i32;
    let bits = u16::from_le_bytes([*dib.get(14)?, *dib.get(15)?]);
    let compression = u32_at(16)?;
    if header < 40 || width <= 0 || height == 0 || width > 20000 || height.abs() > 20000 || !(bits == 24 || bits == 32)
        || !(compression == 0 || compression == 3)
    {
        return None;
    }
    let offset = header + if compression == 3 && header == 40 { 12 } else { 0 };
    let (w, h) = (width as usize, height.unsigned_abs() as usize);
    let stride = (w * bits as usize).div_ceil(32) * 4;
    let pixels = dib.get(offset..offset + stride * h)?;
    let bpp = bits as usize / 8;
    let any_alpha = bits == 32 && (0..h).any(|y| (0..w).any(|x| pixels[y * stride + x * 4 + 3] != 0));
    let mut rgba = Vec::with_capacity(w * h * 4);
    for row in 0..h {
        let y = if height > 0 { h - 1 - row } else { row };
        let line = &pixels[y * stride..y * stride + w * bpp];
        for px in line.chunks_exact(bpp) {
            let a = if any_alpha { px[3] } else { 255 };
            rgba.extend_from_slice(&[px[2], px[1], px[0], a]);
        }
    }
    let mut out = Vec::new();
    {
        let mut enc = png::Encoder::new(&mut out, w as u32, h as u32);
        enc.set_color(png::ColorType::Rgba);
        enc.set_depth(png::BitDepth::Eight);
        enc.set_compression(png::Compression::Fast);
        let mut writer = enc.write_header().ok()?;
        writer.write_image_data(&rgba).ok()?;
    }
    Some(out)
}

/// PNG → 32비트 아래에서 위로 쌓인 CF_DIB(대부분 프로그램이 읽는 형식).
pub fn png_to_dib(data: &[u8]) -> Option<Vec<u8>> {
    let mut decoder = png::Decoder::new(data);
    decoder.set_transformations(png::Transformations::EXPAND | png::Transformations::STRIP_16);
    let mut reader = decoder.read_info().ok()?;
    let mut buf = vec![0; reader.output_buffer_size()];
    let info = reader.next_frame(&mut buf).ok()?;
    let (w, h) = (info.width as usize, info.height as usize);
    let channels = info.color_type.samples();
    let mut out = Vec::with_capacity(40 + w * h * 4);
    for v in [40u32, w as u32, h as u32] {
        out.extend_from_slice(&v.to_le_bytes());
    }
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&32u16.to_le_bytes());
    out.extend_from_slice(&[0u8; 24]); // BI_RGB, 크기, 해상도, 색 수
    for y in (0..h).rev() {
        let line = &buf[y * info.line_size..y * info.line_size + w * channels];
        for px in line.chunks_exact(channels) {
            let (r, g, b, a) = match channels {
                1 => (px[0], px[0], px[0], 255),
                2 => (px[0], px[0], px[0], px[1]),
                3 => (px[0], px[1], px[2], 255),
                _ => (px[0], px[1], px[2], px[3]),
            };
            out.extend_from_slice(&[b, g, r, a]);
        }
    }
    Some(out)
}

pub fn png_size(data: &[u8]) -> Option<(u32, u32)> {
    let w = data.get(16..20)?;
    let h = data.get(20..24)?;
    Some((u32::from_be_bytes([w[0], w[1], w[2], w[3]]), u32::from_be_bytes([h[0], h[1], h[2], h[3]])))
}

/// 팝업·관리 화면에 보일 한 줄 미리보기.
pub fn preview(kind: &str, payload: &[u8]) -> String {
    match kind {
        "text" => {
            let text = String::from_utf8_lossy(payload);
            let line: String = text.split_whitespace().collect::<Vec<_>>().join(" ");
            let mut short: String = line.chars().take(200).collect();
            if line.chars().count() > 200 {
                short.push('…');
            }
            short
        }
        "files" => {
            let text = String::from_utf8_lossy(payload);
            let names: Vec<&str> = text.split('\n').filter(|p| !p.is_empty())
                .map(|p| p.rsplit('\\').next().unwrap_or(p)).collect();
            let shown = names.iter().take(3).copied().collect::<Vec<_>>().join(", ");
            if names.len() > 3 { format!("파일 {}개: {shown} …", names.len()) } else { format!("파일 {}개: {shown}", names.len()) }
        }
        "image" => match png_size(payload) {
            Some((w, h)) => format!("그림 {w}×{h}"),
            None => "그림".into(),
        },
        _ => String::new(),
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    fn dib(w: i32, h: i32, bits: u16, pixel: &[u8]) -> Vec<u8> {
        let stride = ((w as usize * bits as usize).div_ceil(32)) * 4;
        let mut d = Vec::new();
        for v in [40u32, w as u32, h as u32] {
            d.extend_from_slice(&v.to_le_bytes());
        }
        d.extend_from_slice(&1u16.to_le_bytes());
        d.extend_from_slice(&bits.to_le_bytes());
        d.extend_from_slice(&[0u8; 24]);
        for _ in 0..h.unsigned_abs() {
            let mut line = Vec::new();
            for _ in 0..w {
                line.extend_from_slice(pixel);
            }
            line.resize(stride, 0);
            d.extend_from_slice(&line);
        }
        d
    }

    #[test]
    fn dib_png_roundtrip() {
        let png = dib_to_png(&dib(3, 2, 24, &[10, 20, 30])).unwrap();
        assert_eq!(png_size(&png), Some((3, 2)));
        let back = png_to_dib(&png).unwrap();
        assert_eq!(&back[40..44], &[10, 20, 30, 255]); // BGRA, 알파 없으면 불투명
        assert!(dib_to_png(&dib(2, 2, 8, &[1])).is_none());
        assert!(dib_to_png(&[0u8; 10]).is_none());
        let top_down = dib_to_png(&dib(1, -1, 32, &[1, 2, 3, 0])).unwrap();
        assert_eq!(png_size(&top_down), Some((1, 1)));
    }

    #[test]
    fn formats_pack() {
        let packed = pack_formats(&[("HTML Format".into(), b"<b>x</b>".to_vec()), ("Rich Text Format".into(), vec![])]);
        let back = unpack_formats(&packed);
        assert_eq!(back.len(), 2);
        assert_eq!(back[0], ("HTML Format".to_string(), b"<b>x</b>".to_vec()));
        assert!(unpack_formats(&[]).is_empty());
        assert!(unpack_formats(&packed[..7]).is_empty());
        assert!(pack_formats(&[]).is_empty());
    }

    #[test]
    fn previews() {
        assert_eq!(preview("text", "  가나\n\t다  ".as_bytes()), "가나 다");
        assert_eq!(preview("files", "C:\\a\\1.hwpx\nC:\\b\\2.pdf".as_bytes()), "파일 2개: 1.hwpx, 2.pdf");
        assert!(preview("text", "가".repeat(300).as_bytes()).ends_with('…'));
    }
}
