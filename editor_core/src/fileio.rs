//! 인코딩(UTF-8·UTF-8 BOM·UTF-16 LE/BE·CP949) 감지/변환, 줄바꿈 감지/변환, 임시 파일 후 교체 저장.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Encoding {
    Utf8,
    Utf8Bom,
    Utf16Le,
    Utf16Be,
    /// 통합완성형(옛 한글 txt, EUC-KR 계열).
    Cp949,
}

impl Encoding {
    pub fn name(self) -> &'static str {
        match self {
            Encoding::Utf8 => "UTF-8",
            Encoding::Utf8Bom => "UTF-8 BOM",
            Encoding::Utf16Le => "UTF-16 LE",
            Encoding::Utf16Be => "UTF-16 BE",
            Encoding::Cp949 => "CP949",
        }
    }
    /// 정식 이름과 흔한 별칭(대소문자·공백·하이픈·밑줄 무시)을 받는다.
    pub fn from_name(s: &str) -> Option<Encoding> {
        let key: String = s.chars().filter(|c| !matches!(c, ' ' | '-' | '_')).flat_map(char::to_lowercase).collect();
        Some(match key.as_str() {
            "utf8" => Encoding::Utf8,
            "utf8bom" | "utf8sig" => Encoding::Utf8Bom,
            "utf16le" => Encoding::Utf16Le,
            "utf16be" => Encoding::Utf16Be,
            "cp949" | "euckr" | "ms949" | "uhc" | "windows949" => Encoding::Cp949,
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

/// 바이트를 글자로 풀어 쓴다. 감지 순서: BOM(UTF-8/UTF-16 LE/BE) → BOM 없는 엄격한 UTF-8(순수 ASCII 포함)
/// → CP949. 모두 아니면 오류. (BOM 없는 UTF-16은 감지하지 않는다. 필요하면 `decode_as`로 지정한다.)
pub fn decode(bytes: &[u8]) -> Result<(String, Encoding), String> {
    if let Some(rest) = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]) {
        let s = std::str::from_utf8(rest).map_err(|e| format!("UTF-8 오류(위치 {})", e.valid_up_to() + 3))?;
        return Ok((s.to_string(), Encoding::Utf8Bom));
    }
    for (bom, enc) in [([0xFF, 0xFE], Encoding::Utf16Le), ([0xFE, 0xFF], Encoding::Utf16Be)] {
        if let Some(rest) = bytes.strip_prefix(&bom) {
            return decode_utf16(rest, enc).map(|s| (s, enc));
        }
    }
    match std::str::from_utf8(bytes) {
        Ok(s) => Ok((s.to_string(), Encoding::Utf8)),
        Err(e8) => match crate::cp949::decode(bytes) {
            Ok(s) => Ok((s, Encoding::Cp949)),
            Err(p) => Err(format!(
                "UTF-8도 CP949(EUC-KR)도 아닌 바이트가 있습니다(UTF-8 오류 위치 {}, CP949 오류 위치 {p}).",
                e8.valid_up_to()
            )),
        },
    }
}

fn decode_utf16(rest: &[u8], enc: Encoding) -> Result<String, String> {
    if rest.len() % 2 != 0 {
        return Err("UTF-16 길이가 홀수입니다.".into());
    }
    let units = rest.chunks_exact(2).map(|c| {
        if enc == Encoding::Utf16Le { u16::from_le_bytes([c[0], c[1]]) } else { u16::from_be_bytes([c[0], c[1]]) }
    });
    let s: Result<String, _> = char::decode_utf16(units).collect();
    s.map_err(|_| "UTF-16 대리 쌍 오류".to_string())
}

/// 인코딩을 사용자가 지정해 연다(자동 감지가 틀렸을 때). BOM이 있으면 지정한 인코딩의 BOM만 벗긴다.
pub fn decode_as(bytes: &[u8], enc: Encoding) -> Result<String, String> {
    match enc {
        Encoding::Utf8 | Encoding::Utf8Bom => {
            let rest = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]).unwrap_or(bytes);
            std::str::from_utf8(rest).map(str::to_string).map_err(|e| format!("UTF-8이 아닌 바이트가 있습니다(위치 {}).", e.valid_up_to()))
        }
        Encoding::Utf16Le | Encoding::Utf16Be => {
            let bom: &[u8] = if enc == Encoding::Utf16Le { &[0xFF, 0xFE] } else { &[0xFE, 0xFF] };
            decode_utf16(bytes.strip_prefix(bom).unwrap_or(bytes), enc)
        }
        Encoding::Cp949 => crate::cp949::decode(bytes).map_err(|p| format!("CP949가 아닌 바이트가 있습니다(위치 {p}).")),
    }
}

/// 글을 지정한 인코딩의 바이트로 만든다. CP949로 표현할 수 없는 글자가 있으면 오류(몰래 바꾸지 않는다).
pub fn encode(s: &str, enc: Encoding) -> Result<Vec<u8>, String> {
    Ok(match enc {
        Encoding::Utf8 => s.as_bytes().to_vec(),
        Encoding::Utf8Bom => {
            let mut v = Vec::with_capacity(s.len() + 3);
            v.extend_from_slice(&[0xEF, 0xBB, 0xBF]);
            v.extend_from_slice(s.as_bytes());
            v
        }
        Encoding::Utf16Le | Encoding::Utf16Be => {
            let le = enc == Encoding::Utf16Le;
            let mut v = Vec::with_capacity(s.len() * 2 + 2);
            v.extend_from_slice(if le { &[0xFF, 0xFE] } else { &[0xFE, 0xFF] });
            for u in s.encode_utf16() {
                v.extend_from_slice(&if le { u.to_le_bytes() } else { u.to_be_bytes() });
            }
            v
        }
        Encoding::Cp949 => crate::cp949::encode(s)
            .map_err(|(pos, c)| format!("CP949로 저장할 수 없는 글자 '{c}'(U+{:04X}, 글 위치 {pos})가 있습니다. UTF-8로 저장하세요.", c as u32))?,
    })
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
