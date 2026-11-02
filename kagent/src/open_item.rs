use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use windows_sys::Win32::Foundation::HWND;
use windows_sys::Win32::UI::Shell::ShellExecuteW;
use windows_sys::Win32::UI::WindowsAndMessaging::SW_SHOWNORMAL;

use crate::util::wide;

const OPEN_DIR: &str = "open";
const FORBIDDEN: &[&str] = &["exe", "com", "bat", "cmd", "ps1", "psm1", "vbs", "vbe", "js", "jse", "wsf", "wsh", "msc", "scr", "pif", "cpl", "hta", "lnk", "url", "reg", "msi", "msp", "dll"];
pub const MAX_WEB_URL_CHARS: usize = 2048;
const WEB_MARKER: &[u8] = b"\0KAGENT-WEB\0";
static NAME_SEQ: AtomicU64 = AtomicU64::new(0);

/// Accept only bounded HTTP(S) URLs without control characters or whitespace.
pub fn safe_web_url(url: &str) -> Option<&str> {
    if url.is_empty() || url.chars().count() > MAX_WEB_URL_CHARS
        || url.chars().any(|c| c.is_control() || c.is_whitespace())
    { return None; }
    let rest = if let Some(rest) = url.strip_prefix("http://") { rest }
        else if let Some(rest) = url.strip_prefix("https://") { rest }
        else { return None };
    let authority = rest.split(['/', '?', '#']).next().unwrap_or("");
    if authority.is_empty() || authority.starts_with('.') || authority.ends_with('.') { return None; }
    Some(url)
}

pub fn classify_web_text(text: &str) -> Option<String> {
    let trimmed = text.trim();
    if let Some(url) = trimmed.strip_prefix("www.") {
        let normalized = format!("https://{trimmed}");
        let _ = url;
        return safe_web_url(&normalized).map(str::to_owned);
    }
    safe_web_url(trimmed).map(str::to_owned)
}

/// Extract a bounded SourceURL field from CF_HTML bytes.
pub fn source_url_from_html(html: &[u8]) -> Option<String> {
    let header_end = html.iter().position(|&b| b == b'<').unwrap_or(html.len());
    let header = String::from_utf8_lossy(&html[..header_end]);
    if header.contains('\n') && !header.contains("\r\n") { return None; }
    let normalized = header.replace("\r\n", "\n");
    if normalized.lines().any(|line| line.trim_start().starts_with("javascript:") || line.trim_start().starts_with("file:") || line.trim_start().starts_with("ms-")) { return None; }
    let value = normalized.lines().find_map(|line| {
        let (key, value) = line.split_once(':')?;
        key.trim().eq_ignore_ascii_case("SourceURL").then_some(value.trim())
    })?;
    safe_web_url(value).map(str::to_owned)
}

pub fn encode_web_extra(formats: &[(String, Vec<u8>)], url: &str) -> Vec<u8> {
    let mut out = WEB_MARKER.to_vec();
    out.extend_from_slice(url.as_bytes());
    out.push(0);
    out.extend_from_slice(&crate::clip::pack_formats(formats));
    out
}

pub fn web_url_from_extra(extra: &[u8]) -> Option<String> {
    let rest = extra.strip_prefix(WEB_MARKER)?;
    let end = rest.iter().position(|&b| b == 0)?;
    let url = std::str::from_utf8(&rest[..end]).ok()?;
    safe_web_url(url).map(str::to_owned)
}

pub fn formats_from_extra(extra: &[u8]) -> Vec<(String, Vec<u8>)> {
    if let Some(rest) = extra.strip_prefix(WEB_MARKER) {
        let Some(end) = rest.iter().position(|&b| b == 0) else { return Vec::new() };
        return crate::clip::unpack_formats(&rest[end + 1..]);
    }
    crate::clip::unpack_formats(extra)
}

#[link(name = "bcrypt")]
unsafe extern "system" {
    fn BCryptGenRandom(algorithm: *mut std::ffi::c_void, buffer: *mut u8, length: u32, flags: u32) -> i32;
}

fn extension(path: &str) -> Option<String> {
    Path::new(path).extension().and_then(|s| s.to_str()).map(str::to_ascii_lowercase)
}

fn forbidden(path: &str) -> bool {
    extension(path).is_some_and(|ext| FORBIDDEN.contains(&ext.as_str()))
}

fn temp_name(dir: &Path, ext: &str) -> PathBuf {
    let mut random = [0u8; 16];
    let status = unsafe { BCryptGenRandom(std::ptr::null_mut(), random.as_mut_ptr(), random.len() as u32, 2) };
    if status != 0 {
        use std::io::Read;
        if std::fs::File::open("/dev/urandom").and_then(|mut f| f.read_exact(&mut random)).is_err() {
            let seed = format!("{}:{}:{}", std::process::id(), crate::util::now(), NAME_SEQ.fetch_add(1, Ordering::Relaxed));
            for (i, b) in seed.bytes().cycle().take(random.len()).enumerate() { random[i] = b ^ (i as u8).wrapping_mul(73); }
        }
    }
    let name = random.iter().map(|b| format!("{b:02x}")).collect::<String>();
    dir.join(format!("{name}.{ext}"))
}

fn temp_bytes(dir: &Path, ext: &str, bytes: &[u8]) -> Result<PathBuf, String> {
    std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    for _ in 0..8 {
        let path = temp_name(dir, ext);
        match std::fs::OpenOptions::new().write(true).create_new(true).open(&path) {
            Ok(mut file) => {
                use std::io::Write;
                if let Err(e) = file.write_all(bytes) { let _ = std::fs::remove_file(&path); return Err(e.to_string()); }
                return Ok(path);
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(e) => return Err(e.to_string()),
        }
    }
    Err("임시 파일 이름을 만들 수 없습니다.".into())
}

pub fn cleanup(data_dir: &str) {
    let path = Path::new(data_dir).join(OPEN_DIR);
    if let Ok(entries) = std::fs::read_dir(path) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_file() { let _ = std::fs::remove_file(p); }
        }
    }
}

fn shell_open(hwnd: HWND, path: &str, verb: &str) -> bool {
    let result = unsafe { ShellExecuteW(hwnd, wide(verb).as_ptr(), wide(path).as_ptr(), std::ptr::null(), std::ptr::null(), SW_SHOWNORMAL) };
    result as isize > 32
}

fn notify(hwnd: HWND, text: &str) {
    unsafe { windows_sys::Win32::UI::WindowsAndMessaging::MessageBoxW(hwnd, wide(text).as_ptr(), wide("몽땅클립보드").as_ptr(), windows_sys::Win32::UI::WindowsAndMessaging::MB_OK | windows_sys::Win32::UI::WindowsAndMessaging::MB_ICONINFORMATION); }
}

pub fn open(hwnd: HWND, data_dir: &str, kind: &str, data: &[u8], extra: &[u8], choose_app: bool) {
    let url = web_url_from_extra(extra).or_else(|| if kind == "text" { classify_web_text(&String::from_utf8_lossy(data)) } else { None });
    if let Some(url) = url {
        if let Some(url) = safe_web_url(&url) {
            if !shell_open(hwnd, url, "open") { notify(hwnd, "기본 브라우저에서 웹주소를 열지 못했습니다."); }
        }
        return;
    }
    if kind == "files" {
        let paths = String::from_utf8_lossy(data);
        for path in paths.split('\n').filter(|s| !s.is_empty()) {
            if !Path::new(path).exists() { notify(hwnd, &format!("경로가 없습니다:\n{path}")); continue; }
            if forbidden(path) { notify(hwnd, "실행 파일 항목은 여기서 실행할 수 없습니다."); continue; }
            if !shell_open(hwnd, path, if choose_app { "openas" } else { "open" }) { notify(hwnd, &format!("항목을 열지 못했습니다:\n{path}")); }
        }
        return;
    }
    let (ext, contents) = match kind {
        "image" => ("png", data.to_vec()),
        "text" => { let mut b = vec![0xef, 0xbb, 0xbf]; b.extend_from_slice(data); ("txt", b) },
        _ => { notify(hwnd, "지원하지 않는 항목입니다."); return; }
    };
    let path = match temp_bytes(&Path::new(data_dir).join(OPEN_DIR), ext, &contents) {
        Ok(p) => p,
        Err(e) => { notify(hwnd, &format!("임시 파일을 만들지 못했습니다:\n{e}")); return; }
    };
    if !shell_open(hwnd, &path.to_string_lossy(), if choose_app { "openas" } else { "open" }) {
        let _ = std::fs::remove_file(path);
        notify(hwnd, "항목을 열지 못했습니다.");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn executable_extensions_are_blocked_case_insensitively() {
        for p in ["C:\\a.exe", "C:\\b.BAT", "C:\\c.cmd", "C:\\d.ps1", "C:\\e.vbs", "C:\\f.js", "C:\\g.lnk"] { assert!(forbidden(p), "{p}"); }
        assert!(!forbidden("C:\\safe.txt"));
    }

    #[test]
    fn generated_names_are_unpredictable_and_have_expected_extension() {
        let dir = Path::new("C:\\private\\open");
        let a = temp_name(dir, "txt");
        let b = temp_name(dir, "txt");
        assert_eq!(a.extension().unwrap(), "txt");
        assert_ne!(a, b);
        assert_eq!(a.parent().unwrap(), dir);
    }

    #[test]
    fn utf8_text_is_written_with_bom() {
        let dir = std::env::temp_dir().join(format!("kagent-open-{}", std::process::id()));
        let path = temp_bytes(&dir, "txt", &[0xef, 0xbb, 0xbf, b'x']).unwrap();
        assert_eq!(std::fs::read(&path).unwrap(), [0xef, 0xbb, 0xbf, b'x']);
        let _ = std::fs::remove_dir_all(dir);
    }

    #[test]
    fn web_text_classification_and_scheme_safety() {
        assert_eq!(classify_web_text("  www.example.com/path  ").as_deref(), Some("https://www.example.com/path"));
        assert_eq!(classify_web_text("https://example.com").as_deref(), Some("https://example.com"));
        for bad in ["file:///x", "javascript:alert(1)", "ms-settings:", "https://a.com\nnext", "https://a.com\u{7f}"] {
            assert!(classify_web_text(bad).is_none(), "{bad:?}");
        }
        assert!(classify_web_text(&format!("https://{}", "a".repeat(2048))).is_none());
    }

    #[test]
    fn cf_html_source_url_is_parsed_and_validated() {
        assert_eq!(source_url_from_html(b"Version:1.0\r\nStartHTML:00000097\r\nSourceURL:https://example.com/a\r\n<html>"), Some("https://example.com/a".into()));
        assert!(source_url_from_html(b"Version:1.0\r\nSourceURL:file:///secret\r\n<html>").is_none());
        assert!(source_url_from_html(b"Version:1.0\r\nSourceURL:https://a.com\njavascript:bad\r\n<html>").is_none());
    }
}
