//! DPAPI(현재 사용자) 암호화. 앱(파이썬)도 같은 사용자·같은 엔트로피로 풀 수 있다.

use windows_sys::Win32::Foundation::{HLOCAL, LocalFree};
use windows_sys::Win32::Security::Cryptography::{
    CRYPT_INTEGER_BLOB, CRYPTPROTECT_UI_FORBIDDEN, CryptProtectData, CryptUnprotectData,
};

/// 앱 쪽(docfit_app/kagent_client.py)과 같은 값이어야 한다.
pub const ENTROPY: &[u8] = b"HwpAutoDocFit.kagent.v1";

fn blob(data: &[u8]) -> CRYPT_INTEGER_BLOB {
    CRYPT_INTEGER_BLOB { cbData: data.len() as u32, pbData: data.as_ptr() as *mut u8 }
}

fn take(out: CRYPT_INTEGER_BLOB) -> Vec<u8> {
    let v = unsafe { std::slice::from_raw_parts(out.pbData, out.cbData as usize) }.to_vec();
    unsafe { LocalFree(out.pbData as HLOCAL) };
    v
}

pub fn protect(data: &[u8]) -> Option<Vec<u8>> {
    let input = blob(data);
    let entropy = blob(ENTROPY);
    let mut out = CRYPT_INTEGER_BLOB { cbData: 0, pbData: std::ptr::null_mut() };
    let ok = unsafe {
        CryptProtectData(&input, std::ptr::null(), &entropy, std::ptr::null(), std::ptr::null(),
                         CRYPTPROTECT_UI_FORBIDDEN, &mut out)
    };
    (ok != 0).then(|| take(out))
}

pub fn unprotect(data: &[u8]) -> Option<Vec<u8>> {
    let input = blob(data);
    let entropy = blob(ENTROPY);
    let mut out = CRYPT_INTEGER_BLOB { cbData: 0, pbData: std::ptr::null_mut() };
    let ok = unsafe {
        CryptUnprotectData(&input, std::ptr::null_mut(), &entropy, std::ptr::null(), std::ptr::null(),
                           CRYPTPROTECT_UI_FORBIDDEN, &mut out)
    };
    (ok != 0).then(|| take(out))
}

#[cfg(test)]
mod tests {
    #[test]
    fn roundtrip() {
        let secret = "복사한 비밀 내용".as_bytes();
        let sealed = super::protect(secret).unwrap();
        assert!(!sealed.windows(secret.len()).any(|w| w == secret));
        assert_eq!(super::unprotect(&sealed).unwrap(), secret);
        assert!(super::unprotect(b"garbage").is_none());
    }
}
