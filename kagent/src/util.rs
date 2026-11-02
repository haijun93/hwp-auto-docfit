//! 작은 도움 함수들.

pub fn wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

pub fn now() -> f64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0)
}

/// %LOCALAPPDATA%\HwpAutoDocFit\kagent (KAGENT_DATA로 바꿀 수 있음 — 시험용).
pub fn data_dir() -> String {
    if let Ok(root) = std::env::var("KAGENT_TEST_ROOT") {
        return root;
    }
    if let Ok(dir) = std::env::var("KAGENT_DATA") {
        return dir;
    }
    let base = std::env::var("LOCALAPPDATA").unwrap_or_else(|_| ".".into());
    format!("{base}\\HwpAutoDocFit\\kagent")
}

/// 시험 실행은 기본 인스턴스와 충돌하지 않는 별도 커널 객체 이름을 쓴다.
pub fn instance_suffix() -> Option<String> {
    std::env::var("KAGENT_TEST_ROOT").ok().map(|root| {
        let hash = root.encode_utf16().fold(0xcbf29ce484222325u64, |h, c| (h ^ c as u64).wrapping_mul(0x100000001b3));
        format!(".test.{hash:016x}")
    })
}

pub fn base64(data: &[u8]) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let b = [chunk[0], *chunk.get(1).unwrap_or(&0), *chunk.get(2).unwrap_or(&0)];
        let n = (b[0] as u32) << 16 | (b[1] as u32) << 8 | b[2] as u32;
        for i in 0..4 {
            if i <= chunk.len() {
                out.push(T[(n >> (18 - 6 * i) & 63) as usize] as char);
            } else {
                out.push('=');
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_root_is_the_private_data_directory_and_changes_instance_name() {
        let root = std::env::temp_dir().join(format!("kagent-root-{}", std::process::id()));
        std::fs::create_dir_all(&root).unwrap();
        unsafe { std::env::set_var("KAGENT_TEST_ROOT", &root); }
        assert_eq!(data_dir(), root.to_string_lossy());
        let first = instance_suffix().unwrap();
        unsafe { std::env::set_var("KAGENT_TEST_ROOT", root.join("other")); }
        assert_ne!(first, instance_suffix().unwrap());
        unsafe { std::env::remove_var("KAGENT_TEST_ROOT"); }
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn b64() {
        assert_eq!(super::base64(b""), "");
        assert_eq!(super::base64(b"f"), "Zg==");
        assert_eq!(super::base64(b"fo"), "Zm8=");
        assert_eq!(super::base64(b"foobar"), "Zm9vYmFy");
    }
}
