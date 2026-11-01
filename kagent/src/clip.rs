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
                let total_count = DragQueryFileW(h, u32::MAX, std::ptr::null_mut(), 0);
                if total_count == 0 || total_count > MAX_HDROP_FILES {
                    return None;
                }
                let count = total_count;
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

pub fn unpack_formats(data: &[u8]) -> Vec<(String, Vec<u8>)> {
    if data.is_empty() {
        return Vec::new();
    }
    let mut cursor: usize = 0;
    let count_end = match cursor.checked_add(4) {
        Some(e) => e,
        None => return Vec::new(),
    };
    let count_bytes = match data.get(cursor..count_end) {
        Some(b) => b,
        None => return Vec::new(),
    };
    cursor = count_end;
    let count = u32::from_le_bytes([count_bytes[0], count_bytes[1], count_bytes[2], count_bytes[3]]) as usize;
    if count == 0 || count > 16 {
        return Vec::new();
    }
    let mut out = Vec::with_capacity(count);
    for _ in 0..count {
        let name_len_end = match cursor.checked_add(4) {
            Some(e) => e,
            None => return Vec::new(),
        };
        let name_len_bytes = match data.get(cursor..name_len_end) {
            Some(b) => b,
            None => return Vec::new(),
        };
        cursor = name_len_end;
        let name_len = u32::from_le_bytes([name_len_bytes[0], name_len_bytes[1], name_len_bytes[2], name_len_bytes[3]]) as usize;
        let name_end = match cursor.checked_add(name_len) {
            Some(e) => e,
            None => return Vec::new(),
        };
        let name_bytes = match data.get(cursor..name_end) {
            Some(b) => b,
            None => return Vec::new(),
        };
        cursor = name_end;
        let name = String::from_utf8_lossy(name_bytes).into_owned();

        let data_len_end = match cursor.checked_add(4) {
            Some(e) => e,
            None => return Vec::new(),
        };
        let data_len_bytes = match data.get(cursor..data_len_end) {
            Some(b) => b,
            None => return Vec::new(),
        };
        cursor = data_len_end;
        let data_len = u32::from_le_bytes([data_len_bytes[0], data_len_bytes[1], data_len_bytes[2], data_len_bytes[3]]) as usize;
        let data_end = match cursor.checked_add(data_len) {
            Some(e) => e,
            None => return Vec::new(),
        };
        let item_data = match data.get(cursor..data_end) {
            Some(b) => b,
            None => return Vec::new(),
        };
        cursor = data_end;
        out.push((name, item_data.to_vec()));
    }
    if cursor != data.len() {
        return Vec::new();
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

pub const MAX_HDROP_FILES: u32 = 10_000;
pub const MAX_DIB_DIMENSION: u32 = 20_000;
pub const MAX_DIB_PIXELS: usize = 4096 * 4096; // 16M 픽셀 한도 (메모리 예산 및 DoS 방어)

#[derive(Debug, PartialEq, Eq)]
pub struct DibLayout {
    pub width: usize,
    pub height: usize,
    pub stride: usize,
    pub pixel_offset: usize,
    pub pixel_bytes: usize,
    pub bytes_per_pixel: usize,
}

pub fn checked_dib_layout(
    width: i32,
    height: i32,
    bits: u16,
    compression: u32,
    header: usize,
    input_len: usize,
) -> Option<DibLayout> {
    if header < 40 {
        return None;
    }
    if width <= 0 || (width as u32) > MAX_DIB_DIMENSION {
        return None;
    }
    if height == 0 || height == i32::MIN || height.unsigned_abs() > MAX_DIB_DIMENSION {
        return None;
    }
    if bits != 24 && bits != 32 {
        return None;
    }
    if compression != 0 && compression != 3 {
        return None;
    }
    let mask_extra = if compression == 3 && header == 40 { 12usize } else { 0usize };
    let pixel_offset = header.checked_add(mask_extra)?;

    let w = width as usize;
    let h = height.unsigned_abs() as usize;
    let bpp = (bits / 8) as usize;

    let total_pixels = w.checked_mul(h)?;
    if total_pixels > MAX_DIB_PIXELS {
        return None;
    }

    let total_bits = w.checked_mul(bits as usize)?;
    let rounded_bits = total_bits.checked_add(31)?;
    let dwords = rounded_bits / 32;
    let stride = dwords.checked_mul(4)?;

    let pixel_bytes = stride.checked_mul(h)?;
    let total_required = pixel_offset.checked_add(pixel_bytes)?;
    if total_required > input_len {
        return None;
    }

    Some(DibLayout {
        width: w,
        height: h,
        stride,
        pixel_offset,
        pixel_bytes,
        bytes_per_pixel: bpp,
    })
}

/// CF_DIB(24·32비트, BI_RGB·BI_BITFIELDS) → PNG. 다른 형식은 None(기록하지 않음).
pub fn dib_to_png(dib: &[u8]) -> Option<Vec<u8>> {
    let u32_at = |o: usize| dib.get(o..o + 4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]));
    let header = u32_at(0)? as usize;
    let width = u32_at(4)? as i32;
    let height = u32_at(8)? as i32;
    let bits = u16::from_le_bytes([*dib.get(14)?, *dib.get(15)?]);
    let compression = u32_at(16)?;

    let layout = checked_dib_layout(width, height, bits, compression, header, dib.len())?;
    let pixels = dib.get(layout.pixel_offset..layout.pixel_offset.checked_add(layout.pixel_bytes)?)?;
    let (w, h) = (layout.width, layout.height);
    let stride = layout.stride;
    let bpp = layout.bytes_per_pixel;

    let rgba_cap = w.checked_mul(h)?.checked_mul(4)?;
    let mut rgba = Vec::with_capacity(rgba_cap);
    let mut any_alpha = false;

    // 픽셀 메모리 1회 선형 순회 (알파 검사 및 변환을 동시 수행)
    for row in 0..h {
        let y = if height > 0 { h - 1 - row } else { row };
        let line_start = y.checked_mul(stride)?;
        let line_len = w.checked_mul(bpp)?;
        let line = pixels.get(line_start..line_start.checked_add(line_len)?)?;
        for px in line.chunks_exact(bpp) {
            let a = if bits == 32 {
                let alpha = px[3];
                if alpha != 0 {
                    any_alpha = true;
                }
                alpha
            } else {
                255
            };
            rgba.extend_from_slice(&[px[2], px[1], px[0], a]);
        }
    }

    // 32비트 DIB이면서 알파 채널이 전부 0인 경우에만 255(불투명)로 일괄 수정
    if bits == 32 && !any_alpha {
        for px in rgba.chunks_exact_mut(4) {
            px[3] = 255;
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
    if info.width == 0 || info.width > MAX_DIB_DIMENSION || info.height == 0 || info.height > MAX_DIB_DIMENSION {
        return None;
    }
    let (w, h) = (info.width as usize, info.height as usize);
    match w.checked_mul(h) {
        Some(p) if p <= MAX_DIB_PIXELS => (),
        _ => return None,
    }
    let channels = info.color_type.samples();
    if channels == 0 || channels > 4 {
        return None;
    }
    let line_len = w.checked_mul(channels)?;
    if line_len > info.line_size {
        return None;
    }
    let expected_buf_len = info.line_size.checked_mul(h)?;
    if buf.len() < expected_buf_len {
        return None;
    }
    let pixel_bytes = w.checked_mul(h)?.checked_mul(4)?;
    let total_dib_len = 40usize.checked_add(pixel_bytes)?;
    let mut out = Vec::with_capacity(total_dib_len);
    for v in [40u32, w as u32, h as u32] {
        out.extend_from_slice(&v.to_le_bytes());
    }
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&32u16.to_le_bytes());
    out.extend_from_slice(&[0u8; 24]); // BI_RGB, 크기, 해상도, 색 수
    for y in (0..h).rev() {
        let line_start = y * info.line_size;
        let line = &buf[line_start..line_start + line_len];
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

        // 32비트 알파 유지 검증
        let alpha_png = dib_to_png(&dib(1, 1, 32, &[10, 20, 30, 128])).unwrap();
        let back_alpha = png_to_dib(&alpha_png).unwrap();
        assert_eq!(&back_alpha[40..44], &[10, 20, 30, 128]);
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
    fn unpack_formats_rejects_truncated_and_trailing_data() {
        let valid = pack_formats(&[
            ("HTML Format".into(), b"<b>x</b>".to_vec()),
            ("Rich Text Format".into(), b"{\\rtf1}".to_vec()),
        ]);
        let ok = unpack_formats(&valid);
        assert_eq!(ok.len(), 2);
        assert_eq!(ok[0], ("HTML Format".into(), b"<b>x</b>".to_vec()));
        assert_eq!(ok[1], ("Rich Text Format".into(), b"{\\rtf1}".to_vec()));

        // 각 필드에서 잘린 데이터는 전체 빈 결과
        for len in 0..valid.len() {
            assert!(unpack_formats(&valid[..len]).is_empty());
        }

        // 후행 바이트가 있는 경우 거부
        let mut with_trailing = valid.clone();
        with_trailing.push(0);
        assert!(unpack_formats(&with_trailing).is_empty());

        // 과다 count (> 16) 거부
        let mut bad_count = (17u32).to_le_bytes().to_vec();
        bad_count.extend_from_slice(&valid[4..]);
        assert!(unpack_formats(&bad_count).is_empty());
    }

    #[test]
    fn dib_layout_rejects_overflow_and_bad_dimensions() {
        // i32::MIN, 0, 음수 폭, 20,001 치수 거부
        assert!(checked_dib_layout(10, i32::MIN, 24, 0, 40, 1000).is_none());
        assert!(checked_dib_layout(0, 10, 24, 0, 40, 1000).is_none());
        assert!(checked_dib_layout(-5, 10, 24, 0, 40, 1000).is_none());
        assert!(checked_dib_layout(10, 0, 24, 0, 40, 1000).is_none());
        assert!(checked_dib_layout(20001, 10, 24, 0, 40, 10_000_000).is_none());
        assert!(checked_dib_layout(10, 20001, 24, 0, 40, 10_000_000).is_none());
        assert!(checked_dib_layout(10, -20001, 24, 0, 40, 10_000_000).is_none());

        // MAX_DIB_PIXELS (16M) 초과 거부 (예: 5000 x 5000 = 25M)
        assert!(checked_dib_layout(5000, 5000, 24, 0, 40, 100_000_000).is_none());

        // 지원하지 않는 bpp 및 압축 거부
        assert!(checked_dib_layout(10, 10, 16, 0, 40, 1000).is_none());
        assert!(checked_dib_layout(10, 10, 24, 1, 40, 1000).is_none());

        // header < 40 거부
        assert!(checked_dib_layout(10, 10, 24, 0, 39, 1000).is_none());

        // 입력 바이트 부족 (잘린 header/mask/pixels)
        let layout = checked_dib_layout(3, 2, 24, 0, 40, 1000).unwrap();
        assert_eq!(layout.stride, 12); // 3 * 3 = 9 bytes -> 12 bytes (div_ceil(32)*4)
        assert_eq!(layout.pixel_bytes, 24);
        assert_eq!(layout.pixel_offset, 40);
        assert!(checked_dib_layout(3, 2, 24, 0, 40, 63).is_none()); // 40 + 24 = 64 bytes 필요
        assert!(checked_dib_layout(3, 2, 24, 0, 40, 64).is_some());

        // top-down (음수 높이) 및 32-bit 변환 지원
        let top_down = checked_dib_layout(4, -5, 32, 0, 40, 200).unwrap();
        assert_eq!(top_down.height, 5);
        assert_eq!(top_down.stride, 16);
    }

    #[test]
    fn png_to_dib_checked_size() {
        let valid_png = dib_to_png(&dib(2, 2, 24, &[10, 20, 30])).unwrap();
        let dib_bytes = png_to_dib(&valid_png).unwrap();
        assert_eq!(dib_bytes.len(), 40 + 2 * 2 * 4);
        let header = u32::from_le_bytes([dib_bytes[0], dib_bytes[1], dib_bytes[2], dib_bytes[3]]);
        assert_eq!(header, 40);

        // 손상된 입력
        assert!(png_to_dib(&[]).is_none());
        assert!(png_to_dib(b"not a png").is_none());
        assert!(png_to_dib(&valid_png[..valid_png.len() - 5]).is_none());
    }

    #[test]
    fn previews() {
        assert_eq!(preview("text", "  가나\n\t다  ".as_bytes()), "가나 다");
        assert_eq!(preview("files", "C:\\a\\1.hwpx\nC:\\b\\2.pdf".as_bytes()), "파일 2개: 1.hwpx, 2.pdf");
        assert!(preview("text", "가".repeat(300).as_bytes()).ends_with('…'));
    }
}
