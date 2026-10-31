//! 폴더 변경 감시: ReadDirectoryChangesW + 완료 포트 한 개, 스레드 한 개.
//! 알림이 올 때만 깨어나고(폴링 없음), 몰려오는 알림은 잠깐(400ms) 모아 한 번에 넘긴다.

use std::collections::HashMap;
use std::sync::Mutex;

use windows_sys::Win32::Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE, WAIT_TIMEOUT, GetLastError};
use windows_sys::Win32::Storage::FileSystem::{
    CreateFileW, FILE_FLAG_BACKUP_SEMANTICS, FILE_FLAG_OVERLAPPED, FILE_LIST_DIRECTORY, FILE_NOTIFY_CHANGE_CREATION,
    FILE_NOTIFY_CHANGE_DIR_NAME, FILE_NOTIFY_CHANGE_FILE_NAME, FILE_NOTIFY_CHANGE_LAST_WRITE, FILE_NOTIFY_CHANGE_SIZE,
    FILE_SHARE_DELETE, FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING, ReadDirectoryChangesW,
};
use windows_sys::Win32::System::IO::{CreateIoCompletionPort, GetQueuedCompletionStatus, OVERLAPPED,
                                     PostQueuedCompletionStatus};

use crate::util::wide;

/// 바뀐 항목(감시 폴더 기준 상대 경로). Overflow는 알림이 넘쳐 그 폴더를 다시 훑어야 함.
#[derive(Debug, Clone, PartialEq)]
pub enum Change {
    Added(String),
    Removed(String),
    Modified(String),
    Overflow,
}

const BUF_BYTES: usize = 64 * 1024;
const QUIET_MS: u32 = 400;
const MAX_WAIT_MS: u128 = 2000;
const MAX_PENDING_CHANGES: usize = 1000;
const STOP_KEY: usize = usize::MAX;

struct Dir {
    overlapped: OVERLAPPED,
    handle: HANDLE,
    buf: Vec<u64>,
    tag: u32,
    subtree: bool,
}

impl Drop for Dir {
    fn drop(&mut self) {
        if !self.handle.is_null() && self.handle != INVALID_HANDLE_VALUE {
            unsafe { CloseHandle(self.handle) };
            self.handle = INVALID_HANDLE_VALUE;
        }
    }
}

// 감시 스레드 하나만 이 핸들·버퍼를 쓴다.
unsafe impl Send for Dir {}

pub struct Watcher {
    port: HANDLE,
    thread: Option<std::thread::JoinHandle<()>>,
}

unsafe impl Send for Watcher {}

static CURRENT: Mutex<Option<Watcher>> = Mutex::new(None);

fn arm(dir: &mut Dir) -> bool {
    dir.overlapped = unsafe { std::mem::zeroed() };
    let filter = FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_DIR_NAME | FILE_NOTIFY_CHANGE_LAST_WRITE
        | FILE_NOTIFY_CHANGE_SIZE | FILE_NOTIFY_CHANGE_CREATION;
    unsafe {
        ReadDirectoryChangesW(dir.handle, dir.buf.as_mut_ptr() as _, BUF_BYTES as u32, dir.subtree as i32, filter,
                              std::ptr::null_mut(), &mut dir.overlapped, None) != 0
    }
}

fn parse(buf: &[u64], bytes: usize) -> Vec<Change> {
    let raw = unsafe { std::slice::from_raw_parts(buf.as_ptr() as *const u8, bytes.min(BUF_BYTES)) };
    let u32_at = |o: usize| raw.get(o..o + 4).map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]));
    let mut out = Vec::new();
    let mut offset = 0usize;
    loop {
        let (Some(next), Some(action), Some(len)) = (u32_at(offset), u32_at(offset + 4), u32_at(offset + 8)) else {
            break;
        };
        let Some(name) = raw.get(offset + 12..offset + 12 + len as usize) else { break };
        let units: Vec<u16> = name.chunks_exact(2).map(|c| u16::from_le_bytes([c[0], c[1]])).collect();
        let path = String::from_utf16_lossy(&units);
        out.push(match action {
            1 | 5 => Change::Added(path),    // ADDED, RENAMED_NEW_NAME
            2 | 4 => Change::Removed(path),  // REMOVED, RENAMED_OLD_NAME
            _ => Change::Modified(path),
        });
        if next == 0 {
            break;
        }
        offset += next as usize;
    }
    out
}

/// 감시를 (다시) 시작한다. roots: (폴더, 표시 번호, 하위 폴더 포함). 빈 목록이면 멈추기만 한다.
pub fn restart(roots: Vec<(String, u32, bool)>, on_batch: impl Fn(Vec<(u32, Change)>) + Send + 'static) {
    stop();
    if roots.is_empty() {
        return;
    }
    let port = unsafe { CreateIoCompletionPort(INVALID_HANDLE_VALUE, std::ptr::null_mut(), 0, 1) };
    if port.is_null() {
        return;
    }
    let mut dirs: Vec<Box<Dir>> = Vec::new();
    for (path, tag, subtree) in roots {
        let handle = unsafe {
            CreateFileW(wide(&path).as_ptr(), FILE_LIST_DIRECTORY, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                        std::ptr::null(), OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED,
                        std::ptr::null_mut())
        };
        if handle == INVALID_HANDLE_VALUE {
            continue;
        }
        let key = dirs.len();
        if unsafe { CreateIoCompletionPort(handle, port, key, 0) }.is_null() {
            unsafe { CloseHandle(handle) };
            continue;
        }
        let mut dir = Box::new(Dir { overlapped: unsafe { std::mem::zeroed() }, handle, buf: vec![0u64; BUF_BYTES / 8],
                                     tag, subtree });
        if !arm(&mut dir) {
            // arm 실패 시 dir이 스코프를 벗어나며 Dir::drop에서 handle이 자동 해제됨
            continue;
        }
        dirs.push(dir);
    }
    let port_value = port as isize;
    let thread = std::thread::Builder::new().name("kagent-watch".into()).stack_size(256 * 1024).spawn(move || {
        unsafe {
            use windows_sys::Win32::System::Threading::{GetCurrentThread, SetThreadPriority,
                                                        THREAD_MODE_BACKGROUND_BEGIN};
            SetThreadPriority(GetCurrentThread(), THREAD_MODE_BACKGROUND_BEGIN);
        }
        let port = port_value as HANDLE;
        let mut pending: HashMap<(u32, String), Change> = HashMap::new();
        let mut overflow: Vec<u32> = Vec::new();
        let mut first_pending: Option<std::time::Instant> = None;
        loop {
            let mut bytes = 0u32;
            let mut key = 0usize;
            let mut ov: *mut OVERLAPPED = std::ptr::null_mut();
            let wait = if pending.is_empty() && overflow.is_empty() { u32::MAX } else { QUIET_MS };
            let ok = unsafe { GetQueuedCompletionStatus(port, &mut bytes, &mut key, &mut ov, wait) };
            if ok == 0 && ov.is_null() && unsafe { GetLastError() } == WAIT_TIMEOUT {
                flush(&mut pending, &mut overflow, &on_batch);
                first_pending = None;
                continue;
            }
            if key == STOP_KEY {
                break;
            }
            let Some(dir) = dirs.get_mut(key) else { continue };
            if ok == 0 {
                continue; // 폴더가 사라짐 등: 이 폴더 감시는 끝난다.
            }
            if bytes == 0 {
                if !overflow.contains(&dir.tag) {
                    overflow.push(dir.tag);
                    // 전체 스캔으로 대체되므로 해당 폴더의 세부 변경을 압축 제거하여 메모리 점유 방지
                    pending.retain(|&(tag, _), _| tag != dir.tag);
                }
            } else {
                for change in parse(&dir.buf, bytes as usize) {
                    let path = match &change {
                        Change::Added(p) | Change::Removed(p) | Change::Modified(p) => p.clone(),
                        Change::Overflow => continue,
                    };
                    // 새로 생긴 뒤 이어서 쓰인 파일은 '생김'으로 남긴다.
                    let slot = pending.entry((dir.tag, path)).or_insert(Change::Overflow);
                    if !(matches!(slot, Change::Added(_)) && matches!(change, Change::Modified(_))) {
                        *slot = change;
                    }
                }
            }
            arm(dir);
            let started = *first_pending.get_or_insert_with(std::time::Instant::now);
            if started.elapsed().as_millis() > MAX_WAIT_MS || pending.len() >= MAX_PENDING_CHANGES {
                flush(&mut pending, &mut overflow, &on_batch);
                first_pending = None;
            }
        }
        // dirs는 스코프 종료 시 Dir::drop으로 각 dir.handle이 자동 해제됨
        unsafe { CloseHandle(port) };
    });
    match thread {
        Ok(t) => {
            *CURRENT.lock().unwrap() = Some(Watcher { port, thread: Some(t) });
        }
        Err(_) => {
            // thread 생성 실패 시 dirs는 클로저와 함께 drop되어 Dir::drop으로 핸들이 자동 해제됨
            unsafe { CloseHandle(port) };
            *CURRENT.lock().unwrap() = None;
        }
    }
}

fn flush(pending: &mut HashMap<(u32, String), Change>, overflow: &mut Vec<u32>,
         on_batch: &impl Fn(Vec<(u32, Change)>)) {
    let mut batch: Vec<(u32, Change)> = overflow.drain(..).map(|t| (t, Change::Overflow)).collect();
    batch.extend(pending.drain().map(|((tag, _), change)| (tag, change)));
    if !batch.is_empty() {
        on_batch(batch);
    }
}

pub fn stop() {
    let old = CURRENT.lock().unwrap().take();
    if let Some(mut w) = old {
        unsafe { PostQueuedCompletionStatus(w.port, 0, STOP_KEY, std::ptr::null()) };
        if let Some(t) = w.thread.take() {
            let _ = t.join();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc::channel;

    #[test]
    fn parse_records() {
        let mut raw = Vec::new();
        for (i, (action, name)) in [(1u32, "a.png"), (4, "old.hwpx")].iter().enumerate() {
            let units: Vec<u8> = name.encode_utf16().flat_map(|u| u.to_le_bytes()).collect();
            let size = (12 + units.len()).div_ceil(4) * 4;
            raw.extend_from_slice(&(if i == 0 { size as u32 } else { 0 }).to_le_bytes());
            raw.extend_from_slice(&action.to_le_bytes());
            raw.extend_from_slice(&(units.len() as u32).to_le_bytes());
            raw.extend_from_slice(&units);
            raw.resize(raw.len().div_ceil(4) * 4, 0);
        }
        let mut buf = vec![0u64; raw.len().div_ceil(8)];
        unsafe { std::ptr::copy_nonoverlapping(raw.as_ptr(), buf.as_mut_ptr() as *mut u8, raw.len()) };
        assert_eq!(parse(&buf, raw.len()), vec![Change::Added("a.png".into()), Change::Removed("old.hwpx".into())]);
    }

    #[test]
    fn watches_real_folder() {
        let dir = std::env::temp_dir().join(format!("kagent-watch-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(dir.join("sub")).unwrap();
        let (tx, rx) = channel();
        let tx = Mutex::new(tx);
        restart(vec![(dir.to_string_lossy().into_owned(), 7, true)], move |batch| {
            let _ = tx.lock().unwrap().send(batch);
        });
        std::thread::sleep(std::time::Duration::from_millis(100));
        std::fs::write(dir.join("sub").join("보고서.hwpx"), b"x").unwrap();
        let batch = rx.recv_timeout(std::time::Duration::from_secs(5)).unwrap();
        stop();
        assert!(batch.iter().any(|(tag, c)| *tag == 7 && *c == Change::Added("sub\\보고서.hwpx".into())), "{batch:?}");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn restart_empty_roots_cleans_up() {
        restart(vec![], |_| {});
        assert!(CURRENT.lock().unwrap().is_none());
        stop();
        assert!(CURRENT.lock().unwrap().is_none());
    }
}
