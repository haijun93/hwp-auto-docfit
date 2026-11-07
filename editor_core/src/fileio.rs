//! 인코딩·줄바꿈 감지/변환, 임시 파일 후 교체 저장.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Encoding {
    Utf8,
    Utf8Bom,
    Utf16Le,
    Utf16Be,
}

impl Encoding {
    pub fn name(self) -> &'static str {
        match self {
            Encoding::Utf8 => "UTF-8",
            Encoding::Utf8Bom => "UTF-8 BOM",
            Encoding::Utf16Le => "UTF-16 LE",
            Encoding::Utf16Be => "UTF-16 BE",
        }
    }
    pub fn from_name(s: &str) -> Option<Encoding> {
        Some(match s {
            "UTF-8" => Encoding::Utf8,
            "UTF-8 BOM" => Encoding::Utf8Bom,
            "UTF-16 LE" => Encoding::Utf16Le,
            "UTF-16 BE" => Encoding::Utf16Be,
            _ => return None,
        })
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LineEnding {
    Lf,
    Crlf,
    Cr,
}

impl LineEnding {
    pub fn name(self) -> &'static str {
        match self {
            LineEnding::Lf => "LF",
            LineEnding::Crlf => "CRLF",
            LineEnding::Cr => "CR",
        }
    }
    pub fn from_name(s: &str) -> Option<LineEnding> {
        Some(match s {
            "LF" => LineEnding::Lf,
            "CRLF" => LineEnding::Crlf,
            "CR" => LineEnding::Cr,
            _ => return None,
        })
    }
}

/// 줄바꿈 감지 결과: 가장 많은 형식(없으면 LF)과 섞여 있는지 여부.
pub fn detect_line_ending(s: &str) -> (LineEnding, bool) {
    let b = s.as_bytes();
    let (mut crlf, mut lf, mut cr) = (0usize, 0usize, 0usize);
    let mut i = 0;
    while i < b.len() {
        match b[i] {
            b'\r' if b.get(i + 1) == Some(&b'\n') => {
                crlf += 1;
                i += 1;
            }
            b'\r' => cr += 1,
            b'\n' => lf += 1,
            _ => {}
        }
        i += 1;
    }
    let kinds = [crlf, lf, cr].iter().filter(|&&n| n > 0).count();
    let le = if crlf == 0 && lf == 0 && cr == 0 {
        LineEnding::Lf
    } else if crlf >= lf && crlf >= cr {
        LineEnding::Crlf
    } else if lf >= cr {
        LineEnding::Lf
    } else {
        LineEnding::Cr
    };
    (le, kinds > 1)
}

/// CRLF·CR를 LF로 통일한다.
pub fn normalize_to_lf(s: &str) -> String {
    if !s.contains('\r') {
        return s.to_string();
    }
    let mut out = String::with_capacity(s.len());
    let mut it = s.chars().peekable();
    while let Some(c) = it.next() {
        if c == '\r' {
            if it.peek() == Some(&'\n') {
                it.next();
            }
            out.push('\n');
        } else {
            out.push(c);
        }
    }
    out
}

pub fn lf_to(s: &str, le: LineEnding) -> String {
    match le {
        LineEnding::Lf => s.to_string(),
        LineEnding::Crlf => s.replace('\n', "\r\n"),
        LineEnding::Cr => s.replace('\n', "\r"),
    }
}

/// 바이트를 글자로 풀어 쓴다. BOM으로 인코딩을 판별하고, BOM이 없으면 엄격한 UTF-8로 본다.
pub fn decode(bytes: &[u8]) -> Result<(String, Encoding), String> {
    if let Some(rest) = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]) {
        let s = std::str::from_utf8(rest).map_err(|e| format!("UTF-8 오류(위치 {})", e.valid_up_to() + 3))?;
        return Ok((s.to_string(), Encoding::Utf8Bom));
    }
    for (bom, enc) in [([0xFF, 0xFE], Encoding::Utf16Le), ([0xFE, 0xFF], Encoding::Utf16Be)] {
        if let Some(rest) = bytes.strip_prefix(&bom) {
            if rest.len() % 2 != 0 {
                return Err("UTF-16 길이가 홀수입니다.".into());
            }
            let units = rest.chunks_exact(2).map(|c| {
                if enc == Encoding::Utf16Le { u16::from_le_bytes([c[0], c[1]]) } else { u16::from_be_bytes([c[0], c[1]]) }
            });
            let s: Result<String, _> = char::decode_utf16(units).collect();
            return s.map(|s| (s, enc)).map_err(|_| "UTF-16 대리 쌍 오류".to_string());
        }
    }
    let s = std::str::from_utf8(bytes).map_err(|e| format!("UTF-8이 아닌 바이트가 있습니다(위치 {}). CP949 등은 지원하지 않습니다.", e.valid_up_to()))?;
    Ok((s.to_string(), Encoding::Utf8))
}

pub fn encode(s: &str, enc: Encoding) -> Vec<u8> {
    match enc {
        Encoding::Utf8 => s.as_bytes().to_vec(),
        Encoding::Utf8Bom => {
            let mut v = vec![0xEF, 0xBB, 0xBF];
            v.extend_from_slice(s.as_bytes());
            v
        }
        Encoding::Utf16Le | Encoding::Utf16Be => {
            let le = enc == Encoding::Utf16Le;
            let mut v = if le { vec![0xFF, 0xFE] } else { vec![0xFE, 0xFF] };
            for u in s.encode_utf16() {
                v.extend_from_slice(&if le { u.to_le_bytes() } else { u.to_be_bytes() });
            }
            v
        }
    }
}

/// 같은 폴더에 임시 파일을 쓰고 디스크에 반영한 뒤 원본 이름으로 교체한다(중간에 끊겨도 원본 보존).
pub fn write_atomic(path: &Path, bytes: &[u8]) -> Result<(), String> {
    if let Some(dir) = path.parent() {
        if !dir.as_os_str().is_empty() {
            fs::create_dir_all(dir).map_err(|e| format!("폴더 만들기 실패: {e}"))?;
        }
    }
    let mut tmp: PathBuf = path.to_path_buf();
    let name = path.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_else(|| "memo".into());
    tmp.set_file_name(format!(".{name}.{}.tmp", std::process::id()));
    let res = (|| -> std::io::Result<()> {
        let mut f = fs::File::create(&tmp)?;
        f.write_all(bytes)?;
        f.sync_all()?;
        drop(f);
        fs::rename(&tmp, path)
    })();
    if let Err(e) = res {
        let _ = fs::remove_file(&tmp);
        return Err(format!("저장 실패: {e}"));
    }
    Ok(())
}
