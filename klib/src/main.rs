//! 가상 관계형 자료함 엔진 `klib.exe` 진입점.
//! 상주하지 않으며 요청 후 60초 유휴 시 자동 종료.

#![windows_subsystem = "windows"]

mod db;
mod json;
mod pipe;
mod util;
mod search;

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use windows_sys::Win32::Foundation::{CloseHandle, ERROR_ALREADY_EXISTS, GetLastError};
use windows_sys::Win32::System::Threading::CreateMutexW;

use crate::db::Database;
use crate::util::{data_dir, now_ms, wide};

fn send_pipe_cmd(cmd_json: &str) -> Option<String> {
    use windows_sys::Win32::Storage::FileSystem::{
        CreateFileW, ReadFile, WriteFile, FILE_GENERIC_READ, FILE_GENERIC_WRITE, OPEN_EXISTING,
    };
    use windows_sys::Win32::Foundation::INVALID_HANDLE_VALUE;

    let pipe_path = wide(&pipe::pipe_name());
    let handle = unsafe {
        CreateFileW(
            pipe_path.as_ptr(),
            FILE_GENERIC_READ | FILE_GENERIC_WRITE,
            0,
            std::ptr::null(),
            OPEN_EXISTING,
            0,
            std::ptr::null_mut(),
        )
    };
    if handle == INVALID_HANDLE_VALUE {
        return None;
    }
    let mut data = cmd_json.as_bytes().to_vec();
    data.push(b'\n');
    let mut written = 0u32;
    unsafe { WriteFile(handle, data.as_ptr(), data.len() as u32, &mut written, std::ptr::null_mut()) };

    let mut buf = [0u8; 4096];
    let mut read_bytes = 0u32;
    let ok = unsafe { ReadFile(handle, buf.as_mut_ptr(), buf.len() as u32, &mut read_bytes, std::ptr::null_mut()) };
    unsafe { CloseHandle(handle) };
    if ok != 0 && read_bytes > 0 {
        String::from_utf8(buf[..read_bytes as usize].to_vec()).ok()
    } else {
        None
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let has = |flag: &str| args.iter().any(|a| a == flag);

    let mutex_name = format!("Local\\HwpAutoDocFit.klib{}", util::instance_suffix().unwrap_or_default());
    let instance_mutex = unsafe { CreateMutexW(std::ptr::null(), 0, wide(&mutex_name).as_ptr()) };
    if instance_mutex.is_null() {
        std::process::exit(1);
    }

    unsafe {
        if GetLastError() == ERROR_ALREADY_EXISTS {
            CloseHandle(instance_mutex);
            if has("--quit") {
                let _ = send_pipe_cmd(r#"{"cmd":"quit"}"#);
            }
            return;
        }
        if has("--quit") {
            CloseHandle(instance_mutex);
            return;
        }
    }

    let dir = data_dir();
    let _ = std::fs::create_dir_all(&dir);
    let db_path = format!("{dir}\\library.db");
    let db = match Database::open(&db_path) {
        Ok(d) => Arc::new(Mutex::new(d)),
        Err(_) => {
            unsafe { CloseHandle(instance_mutex) };
            std::process::exit(2);
        }
    };

    let running = Arc::new(AtomicBool::new(true));
    let last_activity = Arc::new(AtomicU64::new(now_ms()));

    // 유휴 자동 종료 제한 시간(초) - 기본 60초, KLIB_IDLE_SECS 환경변수 지원
    let idle_limit_secs = std::env::var("KLIB_IDLE_SECS")
        .ok()
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(60);

    // Watchdog 스레드: 60초(또는 지정값) 유휴 시 running을 false로 설정하여 정상 정리 종료 유도
    let r_clone = running.clone();
    let act_clone = last_activity.clone();
    std::thread::Builder::new()
        .name("klib-watchdog".into())
        .spawn(move || {
            while r_clone.load(Ordering::Relaxed) {
                std::thread::sleep(Duration::from_millis(500));
                let elapsed = (now_ms().saturating_sub(act_clone.load(Ordering::Relaxed))) / 1000;
                if elapsed >= idle_limit_secs {
                    r_clone.store(false, Ordering::Relaxed);
                    // 서버 루프가 대기에서 깨어나 정리 후 종료될 수 있도록 여유 대기 후 안전 종료
                    std::thread::sleep(Duration::from_millis(1000));
                    std::process::exit(0);
                }
            }
        })
        .ok();

    // Pipe 서버 구동 (메인 스레드 대기)
    pipe::serve(db, running, last_activity);

    unsafe {
        CloseHandle(instance_mutex);
    }
}
