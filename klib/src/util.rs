//! 유틸리티 함수: UTF-16 변환, 시각, 데이터 경로 및 링크/정션 검출.

use std::path::Path;

pub fn wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

pub fn now() -> f64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

pub fn now_ms() -> u64 {
    (now() * 1000.0) as u64
}

/// 데이터 디렉터리 경로 반환. KLIB_TEST_ROOT 환경 변수가 있으면 해당 격리 디렉터리 사용.
pub fn data_dir() -> String {
    if let Ok(root) = std::env::var("KLIB_TEST_ROOT") {
        return root;
    }
    let base = std::env::var("LOCALAPPDATA").unwrap_or_else(|_| ".".into());
    format!("{base}\\HwpAutoDocFit\\library")
}

/// 테스트 환경 격리를 위한 인스턴스 접미사.
pub fn instance_suffix() -> Option<String> {
    std::env::var("KLIB_TEST_ROOT").ok().map(|root| {
        let hash = root
            .encode_utf16()
            .fold(0xcbf29ce484222325u64, |h, c| (h ^ c as u64).wrapping_mul(0x100000001b3));
        format!(".test.{hash:016x}")
    })
}

/// 파일/폴더가 심볼릭 링크 또는 Windows 정션(Reparse Point)인지 검사.
pub fn is_reparse_point(path: &Path) -> bool {
    let Ok(meta) = std::fs::symlink_metadata(path) else {
        return false;
    };
    if meta.file_type().is_symlink() {
        return true;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x00000400;
        if meta.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0 {
            return true;
        }
    }
    false
}

/// 경로 자체 및 상위 모든 구성요소 중 심볼릭 링크 또는 정션이 포함되어 있는지 검사 (지적 1 반영).
pub fn is_or_has_reparse_point(path: &Path) -> bool {
    for ancestor in path.ancestors() {
        if ancestor.as_os_str().is_empty() {
            continue;
        }
        if is_reparse_point(ancestor) {
            return true;
        }
    }
    false
}

/// 파일명 단일 성분 정규화 및 상위 경로 탈출 방지 (지적 4 반영).
pub fn sanitize_filename(name: &str) -> String {
    let s = Path::new(name)
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| name.to_string());
    let cleaned: String = s
        .chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' | '\0'..='\x1f' => '_',
            _ => c,
        })
        .collect();
    let trimmed = cleaned.trim().trim_matches('.');
    if trimmed.is_empty() || trimmed == "." || trimmed == ".." {
        "unnamed".to_string()
    } else {
        trimmed.to_string()
    }
}

/// Base64 디코딩 (그림 사본 저장용)
pub fn base64_decode(input: &str) -> Option<Vec<u8>> {
    let mut out = Vec::new();
    let mut buf = 0u32;
    let mut bits = 0u32;
    for b in input.bytes() {
        let val = match b {
            b'A'..=b'Z' => (b - b'A') as u32,
            b'a'..=b'z' => (b - b'a' + 26) as u32,
            b'0'..=b'9' => (b - b'0' + 52) as u32,
            b'+' => 62,
            b'/' => 63,
            b'=' | b' ' | b'\r' | b'\n' | b'\t' => continue,
            _ => return None,
        };
        buf = (buf << 6) | val;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((buf >> bits) as u8);
        }
    }
    Some(out)
}
