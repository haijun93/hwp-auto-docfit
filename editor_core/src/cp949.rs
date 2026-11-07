//! CP949(통합완성형, UHC, 흔히 EUC-KR이라 부르는 옛 한글 txt 인코딩) 변환. std만 사용.
//!
//! 표는 `cp949_table.rs`(자동 생성, 표준 매핑 17,048자). 1바이트 0x00~0x7F는 ASCII 그대로,
//! 0x81~0xFE로 시작하면 2바이트 글자다. 표에 없는 조합(0x80, 0xFF, 짝이 없는 앞바이트, 미할당 코드)은 오류로 거절해
//! 감지 단계에서 "CP949가 아니다"를 가려낼 수 있게 한다.
//! 라이선스: 표는 코드↔유니코드 대응 사실의 나열이며 외부 소스 코드를 포함하지 않는다(`tools/gen_cp949.py`로 재생성 가능).

use crate::cp949_table::{LEAD_MAX, LEAD_MIN, TABLE, TRAIL_MAX, TRAIL_MIN};
use std::sync::OnceLock;

/// 표에 든 2바이트 글자 수(시험용 확인 값).
pub const MAPPED: usize = crate::cp949_table::MAPPED;

/// 앞바이트·뒤바이트로 유니코드 값을 찾는다. 없으면 `None`.
#[inline]
fn lookup(lead: u8, trail: u8) -> Option<char> {
    if !(LEAD_MIN..=LEAD_MAX).contains(&lead) || !(TRAIL_MIN..=TRAIL_MAX).contains(&trail) {
        return None;
    }
    match TABLE[(lead - LEAD_MIN) as usize][(trail - TRAIL_MIN) as usize] {
        0 => None,
        u => char::from_u32(u as u32),
    }
}

/// 엄격하게 푼다. 실패하면 처음 잘못된 바이트의 위치.
pub fn decode(bytes: &[u8]) -> Result<String, usize> {
    let mut out = String::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        let b = bytes[i];
        if b < 0x80 {
            out.push(b as char);
            i += 1;
        } else {
            let Some(&t) = bytes.get(i + 1) else { return Err(i) };
            let Some(c) = lookup(b, t) else { return Err(i) };
            out.push(c);
            i += 2;
        }
    }
    Ok(out)
}

/// 유니코드 → CP949 역표(BMP 65,536칸, 0 = 없음). 처음 쓸 때 한 번 만든다.
fn reverse() -> &'static [u16] {
    static REV: OnceLock<Box<[u16]>> = OnceLock::new();
    REV.get_or_init(|| {
        let mut v = vec![0u16; 0x10000];
        for (li, row) in TABLE.iter().enumerate() {
            for (ti, &u) in row.iter().enumerate() {
                if u != 0 {
                    v[u as usize] = (((li as u16) + LEAD_MIN as u16) << 8) | (ti as u16 + TRAIL_MIN as u16);
                }
            }
        }
        v.into_boxed_slice()
    })
}

/// 한 글자를 CP949로 바꿀 수 있는지(ASCII 포함).
pub fn can_encode(c: char) -> bool {
    (c as u32) < 0x80 || ((c as u32) < 0x10000 && reverse()[c as usize] != 0)
}

/// 바꿀 수 없는 글자가 있으면 `Err((바이트 위치, 글자))`. 몰래 `?`로 바꾸지 않는다.
pub fn encode(s: &str) -> Result<Vec<u8>, (usize, char)> {
    let rev = reverse();
    let mut out = Vec::with_capacity(s.len());
    for (pos, c) in s.char_indices() {
        let u = c as u32;
        if u < 0x80 {
            out.push(u as u8);
        } else if u < 0x10000 && rev[u as usize] != 0 {
            let code = rev[u as usize];
            out.push((code >> 8) as u8);
            out.push(code as u8);
        } else {
            return Err((pos, c));
        }
    }
    Ok(out)
}

/// 처음 바꿀 수 없는 글자의 (바이트 위치, 글자).
pub fn first_unencodable(s: &str) -> Option<(usize, char)> {
    s.char_indices().find(|&(_, c)| !can_encode(c))
}
