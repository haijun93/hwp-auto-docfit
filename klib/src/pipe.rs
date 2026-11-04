//! Win32 Named Pipe 서버 및 한 줄 JSON 프로토콜 처리 모듈.

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex, OnceLock};

use windows_sys::Win32::Foundation::{
    CloseHandle, ERROR_IO_PENDING, ERROR_PIPE_CONNECTED, GetLastError, HANDLE, HLOCAL, INVALID_HANDLE_VALUE,
    LocalFree, WAIT_OBJECT_0,
};
use windows_sys::Win32::Security::Authorization::{
    ConvertSidToStringSidW, ConvertStringSecurityDescriptorToSecurityDescriptorW, SDDL_REVISION_1,
};
use windows_sys::Win32::Security::{
    GetTokenInformation, PSECURITY_DESCRIPTOR, SECURITY_ATTRIBUTES, TOKEN_QUERY, TOKEN_USER, TokenUser,
};
use windows_sys::Win32::Storage::FileSystem::{
    FILE_FLAG_OVERLAPPED, FlushFileBuffers, PIPE_ACCESS_DUPLEX, ReadFile, WriteFile,
};
use windows_sys::Win32::System::IO::{CancelIo, OVERLAPPED};
use windows_sys::Win32::System::Pipes::{
    ConnectNamedPipe, CreateNamedPipeW, DisconnectNamedPipe, PeekNamedPipe, PIPE_READMODE_BYTE,
    PIPE_REJECT_REMOTE_CLIENTS, PIPE_TYPE_BYTE, PIPE_WAIT,
};
use windows_sys::Win32::System::Threading::{
    CreateEventW, GetCurrentProcess, OpenProcessToken, WaitForSingleObject,
};

use crate::db::Database;
use crate::json::{self, Value};
use crate::util::{now_ms, wide};

const MAX_REQUEST: usize = 64 * 1024;

pub fn user_sid() -> String {
    static SID: OnceLock<String> = OnceLock::new();
    SID.get_or_init(|| unsafe {
        let mut token: HANDLE = std::ptr::null_mut();
        if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) == 0 {
            return String::new();
        }
        let mut buf = vec![0u8; 256];
        let mut len = 0u32;
        let ok = GetTokenInformation(token, TokenUser, buf.as_mut_ptr() as _, buf.len() as u32, &mut len);
        CloseHandle(token);
        if ok == 0 {
            return String::new();
        }
        let user = &*(buf.as_ptr() as *const TOKEN_USER);
        let mut text: *mut u16 = std::ptr::null_mut();
        if ConvertSidToStringSidW(user.User.Sid, &mut text) == 0 {
            return String::new();
        }
        let mut n = 0;
        while *text.add(n) != 0 {
            n += 1;
        }
        let sid = String::from_utf16_lossy(std::slice::from_raw_parts(text, n));
        LocalFree(text as HLOCAL);
        sid
    })
    .clone()
}

pub fn pipe_name() -> String {
    let suffix = crate::util::instance_suffix().unwrap_or_default();
    format!("\\\\.\\pipe\\HwpAutoDocFit.klib{suffix}.{}", user_sid())
}

pub fn serve(db: Arc<Mutex<Database>>, running: Arc<AtomicBool>, last_activity: Arc<AtomicU64>) {
    let sid = user_sid();
    if sid.is_empty() {
        return;
    }
    let sddl = wide(&format!("D:P(A;;GA;;;{sid})(A;;GA;;;SY)"));
    let mut sd: PSECURITY_DESCRIPTOR = std::ptr::null_mut();
    if unsafe { ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl.as_ptr(), SDDL_REVISION_1, &mut sd, std::ptr::null_mut()) } == 0 {
        return;
    }
    let sa = SECURITY_ATTRIBUTES {
        nLength: std::mem::size_of::<SECURITY_ATTRIBUTES>() as u32,
        lpSecurityDescriptor: sd,
        bInheritHandle: 0,
    };
    let name = wide(&pipe_name());

    while running.load(Ordering::Relaxed) {
        // 비동기 OVERLAPPED 파이프 생성 (지적 7 반영)
        let h = unsafe {
            CreateNamedPipeW(
                name.as_ptr(),
                PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
                PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
                4,
                65536,
                65536,
                0,
                &sa,
            )
        };
        if h == INVALID_HANDLE_VALUE {
            std::thread::sleep(std::time::Duration::from_millis(100));
            continue;
        }

        let event = unsafe { CreateEventW(std::ptr::null(), 1, 0, std::ptr::null()) };
        let mut overlapped: OVERLAPPED = unsafe { std::mem::zeroed() };
        overlapped.hEvent = event;

        let connect_res = unsafe { ConnectNamedPipe(h, &mut overlapped) };
        let mut connected = false;

        if connect_res != 0 {
            connected = true;
        } else {
            let err = unsafe { GetLastError() };
            if err == ERROR_PIPE_CONNECTED {
                connected = true;
            } else if err == ERROR_IO_PENDING {
                // 대기 중 종료 신호(running == false)를 200ms 주기로 점검 (지적 7 반영)
                while running.load(Ordering::Relaxed) {
                    let wait_res = unsafe { WaitForSingleObject(event, 200) };
                    if wait_res == WAIT_OBJECT_0 {
                        connected = true;
                        break;
                    }
                }
                if !connected {
                    // 서버 종료 요청으로 대기 취소 및 정상 정리
                    unsafe {
                        CancelIo(h);
                        CloseHandle(event);
                        CloseHandle(h);
                    }
                    break;
                }
            }
        }

        if connected {
            last_activity.store(now_ms(), Ordering::Relaxed);
            if let Some(req_line) = read_line(h, &last_activity, &running) {
                last_activity.store(now_ms(), Ordering::Relaxed);
                let resp = handle_request(&req_line, &db, &running);
                let mut out = resp.into_bytes();
                out.push(b'\n');
                write_all(h, &out);
                unsafe { FlushFileBuffers(h) };
                last_activity.store(now_ms(), Ordering::Relaxed);
            }
            unsafe { DisconnectNamedPipe(h) };
        }

        unsafe {
            CloseHandle(event);
            CloseHandle(h);
        }
    }

    unsafe {
        LocalFree(sd as HLOCAL);
    }
}

/// 개행 전 요청 길이 기준 64 KiB 제한 및 연결 읽기 타임아웃/활동 갱신 (지적 8, 9 반영)
fn read_line(h: HANDLE, last_activity: &AtomicU64, running: &AtomicBool) -> Option<String> {
    let mut data = Vec::new();
    let mut buf = [0u8; 4096];
    let start_time = now_ms();

    loop {
        if !running.load(Ordering::Relaxed) {
            return None;
        }

        // 이미 읽은 버퍼에 개행이 있는지 검사 (개행 전 길이 기준으로만 64 KiB 제한)
        if let Some(pos) = data.iter().position(|&b| b == b'\n') {
            if pos > MAX_REQUEST {
                return None;
            }
            return String::from_utf8(data[..pos].to_vec()).ok();
        }

        // 개행이 아직 없는데 누적 데이터가 이미 64 KiB를 초과한 경우 거부
        if data.len() > MAX_REQUEST {
            return None;
        }

        // 파이프 수신 버퍼 가용 상태 확인
        let mut avail = 0u32;
        let peek_ok = unsafe {
            PeekNamedPipe(
                h,
                std::ptr::null_mut(),
                0,
                std::ptr::null_mut(),
                &mut avail,
                std::ptr::null_mut(),
            )
        };
        if peek_ok == 0 {
            // 파이프 연결 끊김 또는 오류
            break;
        }

        if avail == 0 {
            // 읽기 타임아웃 (30초 동안 아무 데이터도 안 오면 연결 해제)
            if now_ms().saturating_sub(start_time) > 30_000 {
                return None;
            }
            std::thread::sleep(std::time::Duration::from_millis(20));
            continue;
        }

        let to_read = (buf.len() as u32).min(avail);
        let mut n = 0u32;
        if unsafe { ReadFile(h, buf.as_mut_ptr(), to_read, &mut n, std::ptr::null_mut()) } == 0 || n == 0 {
            break;
        }

        // 활동 시각 갱신 (지적 8 반영)
        last_activity.store(now_ms(), Ordering::Relaxed);
        data.extend_from_slice(&buf[..n as usize]);

        if let Some(pos) = data.iter().position(|&b| b == b'\n') {
            if pos > MAX_REQUEST {
                return None;
            }
            return String::from_utf8(data[..pos].to_vec()).ok();
        }
    }

    if let Some(pos) = data.iter().position(|&b| b == b'\n') {
        if pos <= MAX_REQUEST {
            return String::from_utf8(data[..pos].to_vec()).ok();
        }
    }
    None
}

fn write_all(h: HANDLE, mut data: &[u8]) {
    while !data.is_empty() {
        let mut n = 0u32;
        let chunk = data.len().min(1 << 20) as u32;
        if unsafe { WriteFile(h, data.as_ptr(), chunk, &mut n, std::ptr::null_mut()) } == 0 || n == 0 {
            return;
        }
        data = &data[n as usize..];
    }
}

fn ok_val(mut extra: Vec<(&str, Value)>) -> Value {
    extra.insert(0, ("ok", true.into()));
    Value::obj(extra)
}

fn err_val(msg: &str) -> Value {
    Value::obj(vec![("ok", false.into()), ("message", msg.into())])
}

pub fn handle_request(req_str: &str, db: &Mutex<Database>, running: &AtomicBool) -> String {
    let Some(val) = json::parse(req_str) else {
        return json::to_string(&err_val("요청 JSON 구문 분석에 실패했습니다."));
    };

    let cmd = val.str("cmd").unwrap_or("");
    let resp = match cmd {
        "ping" => ok_val(vec![("message", "pong".into()), ("version", env!("CARGO_PKG_VERSION").into())]),

        "box_create" => {
            let name = val.str("name").unwrap_or("");
            let desc = val.str("description").unwrap_or("");
            if name.is_empty() {
                err_val("자료함 이름을 입력하세요.")
            } else {
                let db_guard = db.lock().unwrap();
                match db_guard.box_create(name, desc) {
                    Ok(id) => ok_val(vec![("id", id.into())]),
                    Err(e) => err_val(&e.to_string()),
                }
            }
        }

        "box_list" => {
            let db_guard = db.lock().unwrap();
            match db_guard.box_list() {
                Ok(list) => {
                    let items: Vec<Value> = list
                        .into_iter()
                        .map(|b| {
                            Value::obj(vec![
                                ("id", b.id.into()),
                                ("name", b.name.into()),
                                ("description", b.description.into()),
                                ("created_at", b.created_at.into()),
                                ("updated_at", b.updated_at.into()),
                                ("export_path", b.export_path.map(Value::Str).unwrap_or(Value::Null)),
                                ("item_count", b.item_count.into()),
                            ])
                        })
                        .collect();
                    ok_val(vec![("boxes", Value::Arr(items))])
                }
                Err(e) => err_val(&e.to_string()),
            }
        }

        "box_get" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("자료함 id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            match db_guard.box_get(id) {
                Ok(Some((b, items, rels))) => {
                    let b_val = Value::obj(vec![
                        ("id", b.id.into()),
                        ("name", b.name.into()),
                        ("description", b.description.into()),
                        ("created_at", b.created_at.into()),
                        ("updated_at", b.updated_at.into()),
                        ("export_path", b.export_path.map(Value::Str).unwrap_or(Value::Null)),
                        ("item_count", b.item_count.into()),
                    ]);
                    let it_vals: Vec<Value> = items
                        .into_iter()
                        .map(|it| {
                            Value::obj(vec![
                                ("id", it.id.into()),
                                ("box_id", it.box_id.into()),
                                ("kind", it.kind.into()),
                                ("source_path", it.source_path.into()),
                                ("display_name", it.display_name.into()),
                                ("space", it.space.into()),
                                ("x", it.x.into()),
                                ("y", it.y.into()),
                                ("created_at", it.created_at.into()),
                            ])
                        })
                        .collect();
                    let rel_vals: Vec<Value> = rels
                        .into_iter()
                        .map(|r| {
                            Value::obj(vec![
                                ("id", r.id.into()),
                                ("box_id", r.box_id.into()),
                                ("from_item", r.from_item.into()),
                                ("to_item", r.to_item.into()),
                                ("label", r.label.into()),
                            ])
                        })
                        .collect();
                    ok_val(vec![
                        ("box", b_val),
                        ("items", Value::Arr(it_vals)),
                        ("relations", Value::Arr(rel_vals)),
                    ])
                }
                Ok(None) => err_val("해당 자료함을 찾을 수 없습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "box_update" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("자료함 id가 누락되었습니다."));
            };
            let name = val.str("name").unwrap_or("");
            let desc = val.str("description").unwrap_or("");
            let db_guard = db.lock().unwrap();
            match db_guard.box_update(id, name, desc) {
                Ok(true) => ok_val(vec![]),
                Ok(false) => err_val("해당 자료함이 존재하지 않습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "box_delete" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("자료함 id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            match db_guard.box_delete(id) {
                Ok(true) => ok_val(vec![]),
                Ok(false) => err_val("해당 자료함이 존재하지 않습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "item_add" => {
            let Some(box_id) = val.i64("box_id") else {
                return json::to_string(&err_val("box_id가 누락되었습니다."));
            };
            let kind = val.str("kind").unwrap_or("");
            let source_path = val.str("source_path").unwrap_or("");
            let display_name = val.str("display_name").unwrap_or("");
            let space = val.str("space").unwrap_or("temp");
            let x = val.num("x").unwrap_or(0.0);
            let y = val.num("y").unwrap_or(0.0);
            let content = val.str("content");

            let db_guard = db.lock().unwrap();
            match db_guard.item_add(box_id, kind, source_path, display_name, space, x, y, content) {
                Ok(id) => {
                    let indexing = if kind == "file" {
                        crate::search_index().and_then(|ix| crate::content::index_file(ix, source_path, display_name, box_id).map_err(|e| format!("본문 색인 실패: {e}"))).err()
                    } else { None };
                    let mut extra = vec![("id", id.into())];
                    if let Some(message) = indexing { extra.push(("index_warning", message.into())); }
                    ok_val(extra)
                },
                Err(e) => err_val(&e),
            }
        }

        "search" => {
            let query = val.str("query").unwrap_or("");
            let box_id = val.i64("box_id");
            let limit = val.i64("limit").unwrap_or(20).clamp(1, 200) as usize;
            match crate::search_index().and_then(|ix| ix.search(query, crate::search::SearchOptions { limit: limit.saturating_mul(20).min(4000) }).map_err(|e| e.to_string())) {
                Ok(hits) => {
                    let mut filtered: Vec<Value> = hits.into_iter()
                        .filter(|hit| box_id.map_or(true, |id| hit.box_ids.contains(&id.to_string())))
                        .map(|hit| {
                            let snippets: Vec<Value> = hit.snippets.iter().map(|s| s.clone().into()).collect();
                            let highlights: Vec<Value> = hit.highlighted.iter().map(|s| s.clone().into()).collect();
                            let pages: Vec<Value> = hit.hit_pages.iter()
                                .map(|p| p.map(|v| (v as i64).into()).unwrap_or(Value::Null)).collect();
                            Value::obj(vec![
                                ("path", hit.path.into()), ("name", hit.name.into()),
                                ("snippet", snippets.first().cloned().unwrap_or(Value::Str(String::new()))),
                                ("highlights", Value::Arr(highlights)), ("hits", (hit.paragraph_count as i64).into()),
                                ("page", hit.page.map(|p| (p as i64).into()).unwrap_or(Value::Null)),
                                ("pages", Value::Arr(pages)), ("score", (hit.score as f64).into()),
                            ])
                        }).collect();
                    filtered.truncate(limit);
                    ok_val(vec![("results", Value::Arr(filtered))])
                }
                Err(e) => err_val(&e),
            }
        }

        "index_file" => {
            let path = val.str("path").unwrap_or("");
            let name = val.str("name").unwrap_or_else(|| std::path::Path::new(path).file_name().and_then(|v| v.to_str()).unwrap_or(""));
            let Some(box_id) = val.i64("box_id") else { return json::to_string(&err_val("box_id가 필요합니다.")); };
            match crate::search_index().and_then(|ix| crate::content::index_file(ix, path, name, box_id).map_err(|e| e.to_string())) {
                Ok(()) => ok_val(vec![]), Err(e) => err_val(&e)
            }
        }

        "remove_file" => {
            let path = val.str("path").unwrap_or("");
            match crate::search_index().and_then(|ix| crate::content::remove_file(ix, path).map_err(|e| e.to_string())) {
                Ok(()) => ok_val(vec![]), Err(e) => err_val(&e)
            }
        }

        "item_get" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("item id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            match db_guard.item_get(id) {
                Ok(Some(it)) => ok_val(vec![
                    ("id", it.id.into()),
                    ("box_id", it.box_id.into()),
                    ("kind", it.kind.into()),
                    ("source_path", it.source_path.into()),
                    ("display_name", it.display_name.into()),
                    ("space", it.space.into()),
                    ("x", it.x.into()),
                    ("y", it.y.into()),
                    ("created_at", it.created_at.into()),
                ]),
                Ok(None) => err_val("해당 자료 항목을 찾을 수 없습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "item_update" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("item id가 누락되었습니다."));
            };
            let display_name = val.str("display_name").unwrap_or("");
            let db_guard = db.lock().unwrap();
            match db_guard.item_update(id, display_name) {
                Ok(true) => ok_val(vec![]),
                Ok(false) => err_val("해당 자료 항목이 존재하지 않습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "item_move" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("item id가 누락되었습니다."));
            };
            let space = val.str("space").unwrap_or("temp");
            let x = val.num("x").unwrap_or(0.0);
            let y = val.num("y").unwrap_or(0.0);

            let db_guard = db.lock().unwrap();
            match db_guard.item_move(id, space, x, y) {
                Ok(true) => ok_val(vec![]),
                Ok(false) => err_val("해당 자료 항목이 존재하지 않습니다."),
                Err(e) => err_val(&e),
            }
        }

        "item_delete" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("item id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            let path = db_guard.item_get(id).ok().flatten().map(|it| it.source_path);
            match db_guard.item_delete(id) {
                Ok(true) => {
                    if let Some(path) = path {
                        if let Ok(ix) = crate::search_index() { let _ = crate::content::remove_file(ix, &path); }
                    }
                    ok_val(vec![])
                },
                Ok(false) => err_val("해당 자료 항목이 존재하지 않습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "item_search" => {
            let box_id = val.i64("box_id");
            let query = val.str("query").unwrap_or("");
            let db_guard = db.lock().unwrap();
            match db_guard.item_search(box_id, query) {
                Ok(items) => {
                    let it_vals: Vec<Value> = items
                        .into_iter()
                        .map(|it| {
                            Value::obj(vec![
                                ("id", it.id.into()),
                                ("box_id", it.box_id.into()),
                                ("kind", it.kind.into()),
                                ("source_path", it.source_path.into()),
                                ("display_name", it.display_name.into()),
                                ("space", it.space.into()),
                                ("x", it.x.into()),
                                ("y", it.y.into()),
                                ("created_at", it.created_at.into()),
                            ])
                        })
                        .collect();
                    ok_val(vec![("items", Value::Arr(it_vals))])
                }
                Err(e) => err_val(&e.to_string()),
            }
        }

        "relation_add" => {
            let Some(box_id) = val.i64("box_id") else {
                return json::to_string(&err_val("box_id가 누락되었습니다."));
            };
            let Some(from_item) = val.i64("from_item") else {
                return json::to_string(&err_val("from_item이 누락되었습니다."));
            };
            let Some(to_item) = val.i64("to_item") else {
                return json::to_string(&err_val("to_item이 누락되었습니다."));
            };
            let label = val.str("label").unwrap_or("");

            let db_guard = db.lock().unwrap();
            match db_guard.relation_add(box_id, from_item, to_item, label) {
                Ok(id) => ok_val(vec![("id", id.into())]),
                Err(e) => err_val(&e),
            }
        }

        "relation_delete" => {
            let Some(id) = val.i64("id") else {
                return json::to_string(&err_val("relation id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            match db_guard.relation_delete(id) {
                Ok(true) => ok_val(vec![]),
                Ok(false) => err_val("해당 관계선이 존재하지 않습니다."),
                Err(e) => err_val(&e.to_string()),
            }
        }

        "relation_list" => {
            let Some(box_id) = val.i64("box_id") else {
                return json::to_string(&err_val("box_id가 누락되었습니다."));
            };
            let db_guard = db.lock().unwrap();
            match db_guard.relation_list(box_id) {
                Ok(list) => {
                    let rel_vals: Vec<Value> = list
                        .into_iter()
                        .map(|r| {
                            Value::obj(vec![
                                ("id", r.id.into()),
                                ("box_id", r.box_id.into()),
                                ("from_item", r.from_item.into()),
                                ("to_item", r.to_item.into()),
                                ("label", r.label.into()),
                            ])
                        })
                        .collect();
                    ok_val(vec![("relations", Value::Arr(rel_vals))])
                }
                Err(e) => err_val(&e.to_string()),
            }
        }

        "box_export" => {
            let Some(box_id) = val.i64("box_id") else {
                return json::to_string(&err_val("box_id가 누락되었습니다."));
            };
            let target_dir = val.str("target_dir").unwrap_or("");
            if target_dir.is_empty() {
                err_val("대상 폴더 경로(target_dir)를 지정하세요.")
            } else {
                let db_guard = db.lock().unwrap();
                match db_guard.box_export(box_id, target_dir) {
                    Ok(count) => ok_val(vec![("count", count.into())]),
                    Err(e) => err_val(&e),
                }
            }
        }

        "quit" => {
            running.store(false, Ordering::Relaxed);
            ok_val(vec![("message", "종료합니다.".into())])
        }

        _ => err_val(&format!("알 수 없는 명령입니다: {cmd}")),
    };

    json::to_string(&resp)
}
