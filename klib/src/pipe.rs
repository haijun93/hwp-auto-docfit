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

/// 노트북 출처 문단을 JSON 행에서 만든다(Python 추출 경로). text·level·table(또는 kind="table")·location(또는 page).
fn nb_paragraphs_from_json(rows: &[Value]) -> Result<Vec<crate::notebook::Paragraph>, String> {
    let mut out = Vec::new();
    for row in rows {
        let Some(text) = row.str("text").or_else(|| row.str("body")) else { return Err("문단마다 text가 필요합니다.".into()) };
        let text = text.trim();
        if text.is_empty() { continue; }
        let table = row.bool("table").unwrap_or(false) || row.str("kind") == Some("table");
        let location = row.str("location").or_else(|| row.str("page")).unwrap_or("").to_string();
        out.push(crate::notebook::Paragraph { source_id: 0, ordinal: out.len() as i64, location, level: row.i64("level").unwrap_or(0).clamp(0, 9), kind: if table { "table" } else { "text" }.into(), body: text.to_string() });
    }
    Ok(out)
}

/// 출처 추가: 기본은 klib가 직접 추출한다(txt·md·hwpx·docx·pptx·xlsx, hwpx·docx는 개요 수준·표 행 포함).
/// 요청에 paragraphs가 있으면(구형 hwp·pdf를 Python이 추출한 경우) 그 문단을 첫 묶음으로 쓴다. 나머지 묶음은 nb_index로 덧붙인다.
fn nb_source_add(val: &Value, db: &Mutex<Database>) -> Value {
    let Some(nb) = val.i64("notebook_id") else { return err_val("notebook_id가 필요합니다.") };
    let Some(source_path) = val.str("source_path").or_else(|| val.str("origin")) else { return err_val("source_path가 필요합니다.") };
    let path = std::path::Path::new(source_path);
    if crate::util::is_or_has_reparse_point(path) { return err_val("심볼릭 링크나 정션 경로는 출처로 추가할 수 없습니다."); }
    if !path.is_file() { return err_val("출처 파일을 찾을 수 없습니다."); }
    let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("").to_ascii_lowercase();
    let paragraphs = match val.arr("paragraphs") {
        Some(rows) => {
            if !matches!(ext.as_str(), "txt" | "md" | "hwpx" | "hwp" | "docx" | "pdf" | "pptx" | "xlsx") { return err_val(&format!("지원하지 않는 출처 형식입니다: {ext}")); }
            match nb_paragraphs_from_json(rows) { Ok(p) => p, Err(e) => return err_val(&e) }
        }
        None => {
            if !matches!(ext.as_str(), "txt" | "md" | "hwpx" | "docx" | "pptx" | "xlsx") { return err_val(&format!("지원하지 않는 출처 형식입니다: {ext}")); }
            match crate::content::extract_blocks(path, &ext) {
                Ok(blocks) => blocks.into_iter().enumerate().map(|(i, b)| crate::notebook::Paragraph { source_id: 0, ordinal: i as i64, location: String::new(), level: b.level, kind: if b.table { "table" } else { "text" }.into(), body: b.text }).collect(),
                Err(e) => return err_val(&e),
            }
        }
    };
    if paragraphs.is_empty() { return err_val("출처에서 본문 문단을 찾지 못했습니다."); }
    let metadata = match std::fs::metadata(path) { Ok(m) => m, Err(e) => return err_val(&e.to_string()) };
    let mtime = metadata.modified().ok().and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok()).map(|d| d.as_millis() as i64).unwrap_or(0);
    let display = val.str("display_name").unwrap_or_else(|| path.file_name().and_then(|s| s.to_str()).unwrap_or(source_path));
    let source = {
        let db_guard = db.lock().unwrap();
        let c = db_guard.connection();
        let id = match crate::notebook::add_source(c, nb, &ext, source_path, display) { Ok(id) => id, Err(e) => return err_val(&e.to_string()) };
        if let Err(e) = crate::notebook::replace_paragraphs(c, id, &paragraphs) { return err_val(&e.to_string()); }
        let _ = c.execute("UPDATE nb_source SET original_size=?1,original_mtime=?2,updated_at=?3 WHERE id=?4", rusqlite::params![metadata.len() as i64, mtime, crate::util::now() as i64, id]);
        match crate::notebook::source_by_id(c, id) { Ok(Some(s)) => s, Ok(None) => return err_val("등록한 출처를 찾을 수 없습니다."), Err(e) => return err_val(&e.to_string()) }
    };
    match crate::search_index().and_then(|ix| ix.replace_notebook_source(nb, &source, &paragraphs).map_err(|e| e.to_string())) {
        Ok(()) => ok_val(vec![("id", source.id.into()), ("paragraph_count", (paragraphs.len() as i64).into())]),
        Err(e) => err_val(&e),
    }
}

/// 출처 다시 색인. paragraphs가 있으면 먼저 그 문단을 끝에 덧붙인다(64 KiB 요청 한도 때문에 나눠 보낸 묶음).
fn nb_index(val: &Value, db: &Mutex<Database>) -> Value {
    let Some(id) = val.i64("source_id") else { return err_val("source_id가 필요합니다.") };
    let Some(nb) = val.i64("notebook_id") else { return err_val("notebook_id가 필요합니다.") };
    let extra = match val.arr("paragraphs").map(nb_paragraphs_from_json) { Some(Ok(p)) => Some(p), Some(Err(e)) => return err_val(&e), None => None };
    let data = {
        let db_guard = db.lock().unwrap();
        let c = db_guard.connection();
        crate::notebook::source_by_id(c, id).map_err(|e| e.to_string())
            .and_then(|s| s.ok_or_else(|| "출처를 찾을 수 없습니다.".to_string()))
            .and_then(|s| {
                if s.notebook_id != nb { return Err("출처가 해당 노트북에 속하지 않습니다.".to_string()); }
                if let Some(extra) = &extra { crate::notebook::append_paragraphs(c, id, extra).map_err(|e| e.to_string())?; }
                let ps = crate::notebook::paragraphs(c, id).map_err(|e| e.to_string())?;
                let s = crate::notebook::source_by_id(c, id).map_err(|e| e.to_string())?.unwrap_or(s);
                Ok((s, ps))
            })
    };
    match data.and_then(|(s, ps)| crate::search_index()?.replace_notebook_source(nb, &s, &ps).map_err(|e| e.to_string()).map(|()| ps.len())) {
        Ok(count) => ok_val(vec![("indexed_paragraphs", (count as i64).into()), ("paragraph_count", (count as i64).into()), ("status", "indexed".into())]),
        Err(e) => err_val(&e),
    }
}

fn ok_val(mut extra: Vec<(&str, Value)>) -> Value {

    extra.insert(0, ("ok", true.into()));

    Value::obj(extra)

}

fn scan_status_val() -> Value {
    let s = crate::scan::GLOBAL.snapshot();
    let n = |v: u64| Value::from(v as i64);
    ok_val(vec![
        ("state", s.state.into()), ("phase", s.phase.into()), ("box_id", s.box_id.into()), ("root", s.root.into()),
        ("discovered", n(s.discovered)), ("total", n(s.total)), ("processed", n(s.processed)),
        ("added", n(s.added)), ("updated", n(s.updated)), ("unchanged", n(s.unchanged)), ("removed", n(s.removed)),
        ("skipped_errors", n(s.skipped_errors)), ("error_samples", Value::Arr(s.error_samples.into_iter().map(Into::into).collect())),
        ("message", s.message.into()), ("elapsed_ms", n(s.elapsed_ms)),
    ])
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

        "nb_create" => {
            let name=val.str("name").unwrap_or(""); let description=val.str("description").unwrap_or(""); let db_guard=db.lock().unwrap();
            match crate::notebook::create(db_guard.connection(),name,description){Ok(id)=>ok_val(vec![("id",id.into())]),Err(e)=>err_val(&e.to_string())}
        }
        "nb_list" => { let db_guard=db.lock().unwrap(); match crate::notebook::list(db_guard.connection()){Ok(rows)=>ok_val(vec![("notebooks",Value::Arr(rows.into_iter().map(|(id,name,description,created,updated)|Value::obj(vec![("id",id.into()),("name",name.into()),("description",description.into()),("created_at",created.into()),("updated_at",updated.into())])).collect()))]),Err(e)=>err_val(&e.to_string())} }
        "nb_update" => { let Some(id)=val.i64("id") else{return json::to_string(&err_val("노트북 id가 필요합니다."))};let db_guard=db.lock().unwrap();match crate::notebook::update(db_guard.connection(),id,val.str("name").unwrap_or(""),val.str("description").unwrap_or("")){Ok(true)=>ok_val(vec![]),Ok(false)=>err_val("노트북을 찾을 수 없습니다."),Err(e)=>err_val(&e.to_string())} }
        "nb_delete" => { let Some(id)=val.i64("id") else{return json::to_string(&err_val("노트북 id가 필요합니다."))};if let Err(e)=crate::search_index().and_then(|ix|ix.remove_notebook(id).map_err(|e|e.to_string())){return json::to_string(&err_val(&e))}let db_guard=db.lock().unwrap();match crate::notebook::delete(db_guard.connection(),id){Ok(true)=>ok_val(vec![]),Ok(false)=>err_val("노트북을 찾을 수 없습니다."),Err(e)=>err_val(&e.to_string())} }
        "nb_source_add" => nb_source_add(&val, db),
        "nb_source_list" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let db_guard=db.lock().unwrap();match crate::notebook::sources(db_guard.connection(),nb){Ok(rows)=>ok_val(vec![("sources",Value::Arr(rows.into_iter().map(|s|Value::obj(vec![("id",s.id.into()),("notebook_id",s.notebook_id.into()),("kind",s.kind.into()),("origin",s.origin.into()),("display_name",s.display_name.into()),("status",s.status.into()),("reason",s.reason.into()),("paragraph_count",s.paragraph_count.into()),("original_size",s.original_size.into()),("original_mtime",s.original_mtime.into())])).collect()))]),Err(e)=>err_val(&e.to_string())} }
        "nb_source_remove" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let Some(id)=val.i64("source_id") else{return json::to_string(&err_val("source_id가 필요합니다."))};{let db_guard=db.lock().unwrap();match crate::notebook::source_by_id(db_guard.connection(),id){Ok(Some(s)) if s.notebook_id==nb=>{},Ok(Some(_))=>return json::to_string(&err_val("출처가 해당 노트북에 속하지 않습니다.")),Ok(None)=>return json::to_string(&err_val("출처를 찾을 수 없습니다.")),Err(e)=>return json::to_string(&err_val(&e.to_string()))}}match crate::search_index().and_then(|ix|ix.remove_notebook_source(id).map_err(|e|e.to_string())){Err(e)=>err_val(&e),Ok(())=>{let db_guard=db.lock().unwrap();match crate::notebook::remove_source(db_guard.connection(),id){Ok(true)=>ok_val(vec![]),Ok(false)=>err_val("출처를 찾을 수 없습니다."),Err(e)=>err_val(&e.to_string())}}} }
        "nb_source_paragraphs" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let Some(id)=val.i64("source_id") else{return json::to_string(&err_val("source_id가 필요합니다."))};let db_guard=db.lock().unwrap();match crate::notebook::source_paragraphs(db_guard.connection(),nb,id){Ok(rows)=>ok_val(vec![("paragraphs",Value::Arr(rows.into_iter().map(|p|Value::obj(vec![("source_id",p.source_id.into()),("ordinal",p.ordinal.into()),("location",p.location.into()),("level",p.level.into()),("kind",p.kind.into()),("body",p.body.into())])).collect()))]),Err(e)=>err_val(&e.to_string())} }
        "nb_index" => nb_index(&val, db),
        "nb_search" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let Some(query)=val.str("query") else{return json::to_string(&err_val("query 문자열이 필요합니다."))};let ids=match val.arr("source_ids"){Some(a)=>{let mut ids=Vec::new();for v in a{if let Value::Num(n)=v{if n.fract()!=0.0{return json::to_string(&err_val("source_ids는 정수 배열이어야 합니다."))}ids.push(*n as i64)}else{return json::to_string(&err_val("source_ids는 정수 배열이어야 합니다."))}}Some(ids)},None=>None};let limit=val.i64("limit").unwrap_or(20).clamp(1,200) as usize;let terms=crate::nb_transform::query_terms(query);let search_query=if terms.is_empty(){query.to_string()}else{terms.join(" ")};match crate::search_index().and_then(|ix|ix.search_notebook(nb,&search_query,ids.as_deref(),limit).map_err(|e|e.to_string())){Ok(hits)=>ok_val(vec![("terms",Value::Arr(terms.into_iter().map(Into::into).collect())),("results",Value::Arr(hits.into_iter().map(|h|Value::obj(vec![("source_id",h.source_id.into()),("ordinal",h.ordinal.into()),("display_name",h.display_name.into()),("location",h.location.into()),("score",(h.score as f64).into()),("body",h.body.into())])).collect()))]),Err(e)=>err_val(&e)} }
        "nb_transform" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let Some(transform_type)=val.str("type") else{return json::to_string(&err_val("type 문자열이 필요합니다."))};let ids=val.arr("source_ids").map(|a|a.iter().filter_map(|v|if let Value::Num(n)=v{Some(*n as i64)}else{None}).collect::<Vec<_>>());let limit=val.i64("limit").unwrap_or(20).clamp(1,200) as usize;let db_guard=db.lock().unwrap();let sources=match crate::notebook::sources(db_guard.connection(),nb){Ok(v)=>v,Err(e)=>return json::to_string(&err_val(&e.to_string()))};let mut paragraphs=Vec::new();for source in sources{if ids.as_ref().is_some_and(|set|!set.contains(&source.id)){continue}match crate::notebook::paragraphs(db_guard.connection(),source.id){Ok(mut p)=>paragraphs.append(&mut p),Err(e)=>return json::to_string(&err_val(&e.to_string()))}}match crate::notebook::transform(&paragraphs,transform_type,limit){Ok(rows)=>ok_val(vec![("results",Value::Arr(rows.into_iter().map(|r|Value::obj(vec![("source_id",r.source_id.into()),("ordinal",r.ordinal.into()),("location",r.location.into()),("level",r.level.into()),("kind",r.kind.into()),("text",r.text.into()),("score",r.score.into())])).collect()))]),Err(e)=>err_val(&e)} }
        "nb_note_save" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let citations=match val.arr("citations"){Some(rows)=>{let mut out=Vec::new();for row in rows{let(Some(s),Some(o),Some(q))=(row.i64("source_id"),row.i64("paragraph_ordinal"),row.str("quote"))else{return json::to_string(&err_val("인용에는 source_id, paragraph_ordinal, quote가 필요합니다."))};out.push((s,o,q.to_string()));}out},None=>Vec::new()};let db_guard=db.lock().unwrap();match crate::notebook::save_note_with_citations(db_guard.connection(),val.i64("id"),nb,val.str("title").unwrap_or(""),val.str("body").unwrap_or(""),&citations){Ok(note)=>ok_val(vec![("id",note.into())]),Err(e)=>err_val(&e.to_string())} }
        "nb_note_list" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let db_guard=db.lock().unwrap();let mut stmt=match db_guard.connection().prepare("SELECT id,title,body,updated_at FROM nb_note WHERE notebook_id=?1 ORDER BY updated_at DESC,id DESC"){Ok(s)=>s,Err(e)=>return json::to_string(&err_val(&e.to_string()))};let rows=stmt.query_map([nb],|r|Ok((r.get::<_,i64>(0)?,r.get::<_,String>(1)?,r.get::<_,String>(2)?,r.get::<_,i64>(3)?)));match rows{Ok(rows)=>{let mut notes=Vec::new();for row in rows{let(id,title,body,updated_at)=match row{Ok(v)=>v,Err(e)=>return json::to_string(&err_val(&e.to_string()))};let citations=match crate::notebook::citations(db_guard.connection(),id){Ok(items)=>Value::Arr(items.into_iter().map(|(source_id,paragraph_ordinal,citation_id,quote)|Value::obj(vec![("id",citation_id.into()),("source_id",source_id.into()),("paragraph_ordinal",paragraph_ordinal.into()),("quote",quote.into())])).collect()),Err(e)=>return json::to_string(&err_val(&e.to_string()))};notes.push(Value::obj(vec![("id",id.into()),("title",title.into()),("body",body.into()),("updated_at",updated_at.into()),("citations",citations)]));}ok_val(vec![("notes",Value::Arr(notes))])},Err(e)=>err_val(&e.to_string())} }
        "nb_note_delete" => {let Some(id)=val.i64("id") else{return json::to_string(&err_val("note id가 필요합니다."))};let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let db_guard=db.lock().unwrap();match db_guard.connection().execute("DELETE FROM nb_note WHERE id=?1 AND notebook_id=?2",[id,nb]){Ok(n) if n>0=>ok_val(vec![]),Ok(_)=>err_val("해당 노트북의 노트를 찾을 수 없습니다."),Err(e)=>err_val(&e.to_string())} }
        "nb_export_md" => {let Some(nb)=val.i64("notebook_id") else{return json::to_string(&err_val("notebook_id가 필요합니다."))};let Some(id)=val.i64("note_id") else{return json::to_string(&err_val("note_id가 필요합니다."))};let db_guard=db.lock().unwrap();match crate::notebook::export_md(db_guard.connection(),nb,id){Ok(Some(markdown))=>ok_val(vec![("markdown",markdown.into())]),Ok(None)=>err_val("노트를 찾을 수 없습니다."),Err(e)=>err_val(&e.to_string())} }

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

        "box_rename" => {

            let Some(id) = val.i64("id") else { return json::to_string(&err_val("box id required")); };

            let name = val.str("name").unwrap_or("");

            match db.lock().unwrap().box_rename(id, name) { Ok(true) => ok_val(vec![]), Ok(false) => err_val("box not found"), Err(e) => err_val(&e.to_string()) }

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

                    let indexing = if matches!(kind, "file" | "text" | "rich_text" | "note") {

                        let source = db_guard.item_get(id).ok().flatten().map(|it| it.source_path).unwrap_or_default();

                        crate::search_index().and_then(|ix| crate::content::index_file(ix, &source, display_name, box_id).map_err(|e| format!("본문 색인 실패: {e}"))).err()

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

            match crate::search_index().and_then(|ix| {

                if let Some(id) = box_id { ix.search_box(id, query, limit).map_err(|e| e.to_string()) }

                else { ix.search(query, crate::search::SearchOptions { limit: limit.saturating_mul(20).min(4000) }).map_err(|e| e.to_string()) }

            }) {

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

        "item_rename" => {

            let Some(id) = val.i64("id") else { return json::to_string(&err_val("item id required")); };

            let name = val.str("display_name").unwrap_or("");

            match db.lock().unwrap().item_rename(id, name) { Ok(true) => ok_val(vec![]), Ok(false) => err_val("item not found"), Err(e) => err_val(&e.to_string()) }

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

            if !query.is_empty() {

                if let Some(box_id) = box_id {

                    let limit = val.i64("limit").unwrap_or(20).clamp(1, 200) as usize;

                    let hits = match crate::search_index().and_then(|ix| ix.search_box(box_id, query, limit).map_err(|e| e.to_string())) {

                        Ok(hits) => hits,

                        Err(e) => return json::to_string(&err_val(&e)),

                    };

                    let mut items = Vec::new();

                    for hit in hits {

                        let db_guard = db.lock().unwrap();

                        if let Ok(Some(item)) = db_guard.item_search(Some(box_id), "").map(|rows| rows.into_iter().find(|row| row.source_path.eq_ignore_ascii_case(&hit.path))) {

                            items.push(Value::obj(vec![

                                ("id", item.id.into()), ("box_id", item.box_id.into()),

                                ("kind", item.kind.into()), ("source_path", item.source_path.into()),

                                ("display_name", item.display_name.into()), ("space", item.space.into()),

                                ("x", item.x.into()), ("y", item.y.into()), ("created_at", item.created_at.into()),

                                ("snippet", hit.snippets.first().cloned().unwrap_or_default().into()),

                            ]));

                        }

                    }

                    return json::to_string(&ok_val(vec![("items", Value::Arr(items))]));

                }

            }

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

        "relation_update" => {

            let Some(id) = val.i64("id") else { return json::to_string(&err_val("relation id required")); };

            let label = val.str("label").unwrap_or("");

            match db.lock().unwrap().relation_update(id, label) {

                Ok(true) => ok_val(vec![]), Ok(false) => err_val("relation not found"), Err(e) => err_val(&e.to_string()),

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

        "box_scan" => {
            let Some(box_id) = val.i64("box_id") else { return json::to_string(&err_val("box_id가 필요합니다.")); };
            let Some(path) = val.str("path") else { return json::to_string(&err_val("path(스캔할 폴더)가 필요합니다.")); };
            let db_path = db.lock().unwrap().connection().path().map(|p| p.to_string()).unwrap_or_default();
            if db_path.is_empty() { return json::to_string(&err_val("DB 파일 경로를 알 수 없습니다.")); }
            let exts: Vec<String> = val.arr("extensions").unwrap_or(&[]).iter()
                .filter_map(|v| if let Value::Str(e) = v { Some(e.trim().to_lowercase()) } else { None })
                .filter(|e| !e.is_empty()).map(|e| if e.starts_with('.') { e } else { format!(".{e}") }).collect();
            match crate::scan::start(&db_path, box_id, path, exts) {
                Ok(()) => ok_val(vec![("started", true.into())]),
                Err(e) => err_val(&e),
            }
        }
        "box_scan_status" => scan_status_val(),
        "box_scan_files" => {
            let Some(box_id) = val.i64("box_id") else { return json::to_string(&err_val("box_id가 필요합니다.")); };
            let offset = val.i64("offset").unwrap_or(0).max(0);
            let limit = val.i64("limit").unwrap_or(1000).clamp(1, 5000);
            let guard = db.lock().unwrap();
            match crate::scan::list_files(guard.connection(), box_id, val.str("path"), offset, limit) {
                Ok(rows) => ok_val(vec![("files", Value::Arr(rows.into_iter().map(|(p, s, m)| Value::obj(vec![("path", p.into()), ("size", s.into()), ("mtime", Value::Num(m as f64 / 1e9))])).collect()))]),
                Err(e) => err_val(&e.to_string()),
            }
        }
        "box_scan_cancel" => ok_val(vec![("cancelling", crate::scan::GLOBAL.request_cancel().into())]),

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
