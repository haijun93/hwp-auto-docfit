//! 자료함 폴더 증분 스캔: 크기·수정 시각이 같은 파일은 기존 행을 그대로 쓰고, 사라진 파일 행은 정리한다.
//! 원본 파일은 메타데이터(크기·수정 시각)만 읽고 내용은 열지 않는다. 한 번에 한 스캔만 돈다.

use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};

use rusqlite::{Connection, params};

const BATCH: usize = 1000;
const CHECK_EVERY: u64 = 256;
const MAX_ERRORS: usize = 20;

pub fn init_schema(c: &Connection) -> rusqlite::Result<()> {
    c.execute_batch(
        "CREATE TABLE IF NOT EXISTS scan_file (
             box_id INTEGER NOT NULL REFERENCES box(id) ON DELETE CASCADE,
             root TEXT NOT NULL,
             path TEXT NOT NULL,
             size INTEGER NOT NULL,
             mtime_ns INTEGER NOT NULL,
             scanned_at REAL NOT NULL,
             PRIMARY KEY (box_id, path)
         );
         CREATE INDEX IF NOT EXISTS idx_scan_file_root ON scan_file(box_id, root);",
    )
}

#[derive(Clone, Default, Debug)]
pub struct Status {
    /// idle | scanning | done | cancelled | error
    pub state: String,
    /// enumerate(폴더 훑기) | reconcile(DB 반영) | ""
    pub phase: String,
    pub box_id: i64,
    pub root: String,
    pub discovered: u64,
    pub total: u64,
    pub processed: u64,
    pub added: u64,
    pub updated: u64,
    pub unchanged: u64,
    pub removed: u64,
    pub skipped_errors: u64,
    pub error_samples: Vec<String>,
    pub message: String,
    pub elapsed_ms: u64,
}

pub struct Shared {
    status: Mutex<Status>,
    cancel: AtomicBool,
    running: AtomicBool,
}

impl Shared {
    pub const fn new() -> Self {
        Shared { status: Mutex::new(Status { state: String::new(), phase: String::new(), box_id: 0, root: String::new(),
            discovered: 0, total: 0, processed: 0, added: 0, updated: 0, unchanged: 0, removed: 0, skipped_errors: 0,
            error_samples: Vec::new(), message: String::new(), elapsed_ms: 0 }),
            cancel: AtomicBool::new(false), running: AtomicBool::new(false) }
    }
    pub fn snapshot(&self) -> Status {
        let mut s = self.status.lock().unwrap().clone();
        if s.state.is_empty() { s.state = "idle".into(); }
        s
    }
    pub fn is_running(&self) -> bool { self.running.load(Ordering::SeqCst) }
    /// 실행 중이면 true(취소 요청이 접수됨).
    pub fn request_cancel(&self) -> bool {
        if self.is_running() { self.cancel.store(true, Ordering::SeqCst); true } else { false }
    }
    fn cancelled(&self) -> bool { self.cancel.load(Ordering::SeqCst) }
    fn update(&self, f: impl FnOnce(&mut Status)) { f(&mut self.status.lock().unwrap()); }
}

/// 프로세스 전역 스캔 상태(pipe 명령이 공유).
pub static GLOBAL: Shared = Shared::new();

pub fn is_running() -> bool { GLOBAL.is_running() }

/// 요청을 검증하고 백그라운드 스레드에서 스캔을 시작한다. 파이프 요청은 곧바로 돌려보낸다.
pub fn start(db_path: &str, box_id: i64, root: &str, exts: Vec<String>) -> Result<(), String> {
    let root = normalize_root(root)?;
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;
    prepare(&conn, box_id)?;
    if GLOBAL.running.swap(true, Ordering::SeqCst) {
        return Err("이미 폴더 스캔이 진행 중입니다.".into());
    }
    GLOBAL.cancel.store(false, Ordering::SeqCst);
    GLOBAL.update(|s| *s = Status { state: "scanning".into(), phase: "enumerate".into(), box_id, root: root.clone(), ..Default::default() });
    let spawned = std::thread::Builder::new().name("klib-scan".into()).spawn(move || {
        let mut conn = conn;
        run_scan_filtered(&mut conn, box_id, &root, &GLOBAL, true, &exts);
        GLOBAL.running.store(false, Ordering::SeqCst);
    });
    if let Err(e) = spawned {
        GLOBAL.running.store(false, Ordering::SeqCst);
        return Err(format!("스캔 스레드 시작 실패: {e}"));
    }
    Ok(())
}

fn normalize_root(root: &str) -> Result<String, String> {
    let trimmed = root.trim();
    if trimmed.is_empty() { return Err("path(스캔할 폴더)가 필요합니다.".into()); }
    let p = Path::new(trimmed);
    if !p.is_dir() { return Err(format!("폴더가 아니거나 없습니다: {trimmed}")); }
    if crate::util::is_or_has_reparse_point(p) { return Err("심볼릭 링크나 정션 폴더는 스캔할 수 없습니다.".into()); }
    Ok(trimmed.trim_end_matches(['\\', '/']).to_string()).map(|s| if s.is_empty() { trimmed.to_string() } else { s })
}

fn prepare(conn: &Connection, box_id: i64) -> Result<(), String> {
    conn.busy_timeout(std::time::Duration::from_secs(10)).map_err(|e| e.to_string())?;
    conn.execute_batch("PRAGMA foreign_keys = ON;").map_err(|e| e.to_string())?;
    init_schema(conn).map_err(|e| e.to_string())?;
    let exists: bool = conn.query_row("SELECT EXISTS(SELECT 1 FROM box WHERE id=?1)", params![box_id], |r| r.get(0)).map_err(|e| e.to_string())?;
    if !exists { return Err(format!("자료함(box_id={box_id})이 존재하지 않습니다.")); }
    Ok(())
}

struct Found { path: String, size: i64, mtime_ns: i64 }

fn mtime_ns(meta: &fs::Metadata) -> i64 {
    meta.modified().ok()
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| d.as_nanos().min(i64::MAX as u128) as i64)
        .unwrap_or(0)
}

fn note_error(sh: &Shared, what: &str) {
    sh.update(|s| { s.skipped_errors += 1; if s.error_samples.len() < MAX_ERRORS { s.error_samples.push(what.to_string()); } });
}

/// 1단계: 폴더 훑기. 링크/정션 폴더는 따라가지 않는다. 읽기 오류가 있었는지(`complete=false`)도 돌려준다.
fn enumerate(root: &str, sh: &Shared, started: &std::time::Instant, exts: &[String]) -> (Vec<Found>, bool, bool) {
    let mut out = Vec::new();
    let mut complete = true;
    let mut stack = vec![std::path::PathBuf::from(root)];
    let mut tick = 0u64;
    while let Some(dir) = stack.pop() {
        let rd = match fs::read_dir(&dir) { Ok(r) => r, Err(e) => { complete = false; note_error(sh, &format!("{}: {e}", dir.display())); continue; } };
        for entry in rd {
            tick += 1;
            if tick % CHECK_EVERY == 0 {
                if sh.cancelled() { return (out, complete, true); }
                let n = out.len() as u64;
                let el = started.elapsed().as_millis() as u64;
                sh.update(|s| { s.discovered = n; s.elapsed_ms = el; });
            }
            let entry = match entry { Ok(e) => e, Err(e) => { complete = false; note_error(sh, &format!("{}: {e}", dir.display())); continue; } };
            let meta = match entry.metadata() { Ok(m) => m, Err(e) => { complete = false; note_error(sh, &format!("{}: {e}", entry.path().display())); continue; } };
            let ft = meta.file_type();
            if ft.is_symlink() { continue; }
            #[cfg(windows)]
            { use std::os::windows::fs::MetadataExt; if meta.file_attributes() & 0x400 != 0 { continue; } }
            if ft.is_dir() { stack.push(entry.path()); }
            else if ft.is_file() && ext_allowed(&entry.path(), exts) {
                out.push(Found { path: entry.path().to_string_lossy().into_owned(), size: meta.len().min(i64::MAX as u64) as i64, mtime_ns: mtime_ns(&meta) });
            }
        }
    }
    (out, complete, false)
}

/// 확장자 목록이 비어 있으면 모두 허용. 목록은 소문자·점 포함(예: ".hwpx")이며 비교는 대소문자를 가리지 않는다.
fn ext_allowed(path: &Path, exts: &[String]) -> bool {
    if exts.is_empty() { return true; }
    match path.extension() {
        Some(e) => { let dotted = format!(".{}", e.to_string_lossy().to_lowercase()); exts.iter().any(|x| *x == dotted) }
        None => false,
    }
}

/// 동기 스캔 본체(스레드와 시험·측정이 함께 쓴다). `incremental=false`면 기존 행을 모두 다시 쓰는 비교 기준선이다.
pub fn run_scan_mode(conn: &mut Connection, box_id: i64, root: &str, sh: &Shared, incremental: bool) {
    run_scan_filtered(conn, box_id, root, sh, incremental, &[])
}

pub fn run_scan_filtered(conn: &mut Connection, box_id: i64, root: &str, sh: &Shared, incremental: bool, exts: &[String]) {
    let started = std::time::Instant::now();
    sh.update(|s| { s.state = "scanning".into(); s.phase = "enumerate".into(); s.box_id = box_id; s.root = root.to_string(); });
    let (found, complete, cancelled) = enumerate(root, sh, &started, exts);
    if cancelled {
        let ms = started.elapsed().as_millis() as u64;
        sh.update(|s| { s.state = "cancelled".into(); s.phase.clear(); s.elapsed_ms = ms; s.message = "취소됨(폴더 훑는 중). DB는 바뀌지 않았습니다.".into(); });
        return;
    }
    let total = found.len() as u64;
    sh.update(|s| { s.phase = "reconcile".into(); s.discovered = total; s.total = total; });

    let result = reconcile(conn, box_id, root, found, complete, sh, &started, incremental);
    let ms = started.elapsed().as_millis() as u64;
    match result {
        Ok(was_cancelled) => sh.update(|s| {
            s.state = if was_cancelled { "cancelled" } else { "done" }.into();
            s.phase.clear(); s.elapsed_ms = ms;
            s.message = if was_cancelled { "취소됨. 이미 반영된 행은 유지되고 사라진 파일 정리는 하지 않았습니다.".into() }
                else if !complete { "일부 폴더를 읽지 못해 사라진 파일 정리는 건너뛰었습니다.".into() } else { String::new() };
        }),
        Err(e) => sh.update(|s| { s.state = "error".into(); s.phase.clear(); s.elapsed_ms = ms; s.message = e; }),
    }
}

pub fn run_scan(conn: &mut Connection, box_id: i64, root: &str, sh: &Shared) { run_scan_mode(conn, box_id, root, sh, true) }

#[allow(clippy::too_many_arguments)]
fn reconcile(conn: &mut Connection, box_id: i64, root: &str, found: Vec<Found>, complete: bool, sh: &Shared,
             started: &std::time::Instant, incremental: bool) -> Result<bool, String> {
    let e = |x: rusqlite::Error| x.to_string();
    let mut known: HashMap<String, (i64, i64)> = HashMap::new();
    {
        let mut st = conn.prepare("SELECT path,size,mtime_ns FROM scan_file WHERE box_id=?1 AND root=?2").map_err(e)?;
        let rows = st.query_map(params![box_id, root], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?, r.get::<_, i64>(2)?))).map_err(e)?;
        for row in rows { let (p, s, m) = row.map_err(e)?; known.insert(p, (s, m)); }
    }
    let now = crate::util::now();
    let mut processed = 0u64;
    let (mut added, mut updated, mut unchanged) = (0u64, 0u64, 0u64);
    let mut seen: std::collections::HashSet<&str> = std::collections::HashSet::with_capacity(found.len());
    for chunk in found.chunks(BATCH) {
        if sh.cancelled() { return Ok(true); }
        let tx = conn.transaction().map_err(e)?;
        {
            let mut up = tx.prepare_cached(
                "INSERT INTO scan_file(box_id,root,path,size,mtime_ns,scanned_at) VALUES(?1,?2,?3,?4,?5,?6) \
                 ON CONFLICT(box_id,path) DO UPDATE SET root=excluded.root,size=excluded.size,mtime_ns=excluded.mtime_ns,scanned_at=excluded.scanned_at").map_err(e)?;
            for f in chunk {
                seen.insert(f.path.as_str());
                match known.get(&f.path) {
                    Some(&(s, m)) if incremental && s == f.size && m == f.mtime_ns => unchanged += 1,
                    old => {
                        up.execute(params![box_id, root, f.path, f.size, f.mtime_ns, now]).map_err(e)?;
                        if old.is_some() { updated += 1 } else { added += 1 }
                    }
                }
            }
        }
        tx.commit().map_err(e)?;
        processed += chunk.len() as u64;
        let el = started.elapsed().as_millis() as u64;
        sh.update(|s| { s.processed = processed; s.added = added; s.updated = updated; s.unchanged = unchanged; s.elapsed_ms = el; });
    }
    let mut removed = 0u64;
    if complete {
        let gone: Vec<&String> = known.keys().filter(|p| !seen.contains(p.as_str())).collect();
        for chunk in gone.chunks(BATCH) {
            if sh.cancelled() { return Ok(true); }
            let tx = conn.transaction().map_err(e)?;
            for p in chunk { removed += tx.execute("DELETE FROM scan_file WHERE box_id=?1 AND path=?2", params![box_id, p]).map_err(e)? as u64; }
            tx.commit().map_err(e)?;
            sh.update(|s| s.removed = removed);
        }
    }
    sh.update(|s| { s.removed = removed; s.processed = processed; });
    Ok(false)
}

/// 한 자료함의 스캔 결과 파일 목록(경로순). `root`를 주면 그 루트 아래 행만 돌려준다.
pub fn list_files(conn: &Connection, box_id: i64, root: Option<&str>, offset: i64, limit: i64) -> rusqlite::Result<Vec<(String, i64, i64)>> {
    let mut st = conn.prepare("SELECT path,size,mtime_ns FROM scan_file WHERE box_id=?1 AND (?2 IS NULL OR root=?2) ORDER BY path LIMIT ?3 OFFSET ?4")?;
    let rows = st.query_map(params![box_id, root, limit, offset], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))?;
    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp(name: &str) -> std::path::PathBuf {
        let d = std::env::temp_dir().join(format!("klib-scan-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }
    fn db(dir: &Path) -> Connection {
        let c = Connection::open(dir.join("t.db")).unwrap();
        c.execute_batch("PRAGMA foreign_keys=ON; CREATE TABLE box(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);").unwrap();
        c.execute("INSERT INTO box(name) VALUES('b')", []).unwrap();
        init_schema(&c).unwrap();
        c
    }
    fn count(c: &Connection) -> i64 { c.query_row("SELECT COUNT(*) FROM scan_file", [], |r| r.get(0)).unwrap() }

    #[test]
    fn incremental_reuses_unchanged_and_cleans_removed() {
        let dir = tmp("inc");
        let src = dir.join("src");
        fs::create_dir_all(src.join("sub")).unwrap();
        for i in 0..5 { fs::write(src.join(format!("a{i}.txt")), b"x").unwrap(); }
        fs::write(src.join("sub").join("b.txt"), b"yy").unwrap();
        let mut c = db(&dir);
        let root = src.to_string_lossy().into_owned();

        let sh = Shared::new();
        run_scan(&mut c, 1, &root, &sh);
        let s = sh.snapshot();
        assert_eq!((s.state.as_str(), s.added, s.unchanged, s.total, s.processed), ("done", 6, 0, 6, 6));
        assert_eq!(count(&c), 6);

        let sh = Shared::new();
        run_scan(&mut c, 1, &root, &sh);
        let s = sh.snapshot();
        assert_eq!((s.added, s.updated, s.unchanged, s.removed), (0, 0, 6, 0));

        fs::write(src.join("a0.txt"), b"changed-size").unwrap();
        fs::remove_file(src.join("a1.txt")).unwrap();
        fs::write(src.join("new.txt"), b"n").unwrap();
        let sh = Shared::new();
        run_scan(&mut c, 1, &root, &sh);
        let s = sh.snapshot();
        assert_eq!((s.added, s.updated, s.unchanged, s.removed), (1, 1, 4, 1));
        assert_eq!(count(&c), 6);
        let gone: i64 = c.query_row("SELECT COUNT(*) FROM scan_file WHERE path LIKE '%a1.txt'", [], |r| r.get(0)).unwrap();
        assert_eq!(gone, 0);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn same_size_but_new_mtime_is_rewritten() {
        let dir = tmp("mtime");
        let src = dir.join("src");
        fs::create_dir_all(&src).unwrap();
        let f = src.join("a.txt");
        fs::write(&f, b"x").unwrap();
        let mut c = db(&dir);
        let root = src.to_string_lossy().into_owned();
        run_scan(&mut c, 1, &root, &Shared::new());
        let file = fs::OpenOptions::new().write(true).open(&f).unwrap();
        file.set_modified(std::time::SystemTime::now() + std::time::Duration::from_secs(3600)).unwrap();
        drop(file);
        let sh = Shared::new();
        run_scan(&mut c, 1, &root, &sh);
        assert_eq!((sh.snapshot().updated, sh.snapshot().unchanged), (1, 0));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn cancel_keeps_rows_and_skips_cleanup() {
        let dir = tmp("cancel");
        let src = dir.join("src");
        fs::create_dir_all(&src).unwrap();
        for i in 0..3 { fs::write(src.join(format!("f{i}.txt")), b"x").unwrap(); }
        let mut c = db(&dir);
        let root = src.to_string_lossy().into_owned();
        run_scan(&mut c, 1, &root, &Shared::new());
        fs::remove_file(src.join("f0.txt")).unwrap();
        let sh = Shared::new();
        sh.running.store(true, Ordering::SeqCst);
        assert!(sh.request_cancel());
        run_scan(&mut c, 1, &root, &sh);
        assert_eq!(sh.snapshot().state, "cancelled");
        assert_eq!(count(&c), 3, "취소하면 사라진 파일 정리를 하지 않는다");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn idle_when_no_scan_and_cancel_is_noop() {
        let sh = Shared::new();
        assert_eq!(sh.snapshot().state, "idle");
        assert!(!sh.request_cancel());
    }

    #[test]
    fn two_roots_in_one_box_are_cleaned_independently() {
        let dir = tmp("roots");
        let (a, b) = (dir.join("a"), dir.join("b"));
        fs::create_dir_all(&a).unwrap();
        fs::create_dir_all(&b).unwrap();
        fs::write(a.join("1.txt"), b"1").unwrap();
        fs::write(b.join("2.txt"), b"2").unwrap();
        let mut c = db(&dir);
        run_scan(&mut c, 1, &a.to_string_lossy(), &Shared::new());
        run_scan(&mut c, 1, &b.to_string_lossy(), &Shared::new());
        assert_eq!(count(&c), 2);
        fs::remove_file(a.join("1.txt")).unwrap();
        run_scan(&mut c, 1, &a.to_string_lossy(), &Shared::new());
        assert_eq!(count(&c), 1, "다른 루트(b)의 행은 건드리지 않는다");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn unreadable_start_dir_does_not_wipe_rows() {
        let dir = tmp("wipe");
        let src = dir.join("src");
        fs::create_dir_all(&src).unwrap();
        fs::write(src.join("a.txt"), b"1").unwrap();
        let mut c = db(&dir);
        let root = src.to_string_lossy().into_owned();
        run_scan(&mut c, 1, &root, &Shared::new());
        fs::remove_dir_all(&src).unwrap();
        let sh = Shared::new();
        run_scan(&mut c, 1, &root, &sh);
        assert_eq!(count(&c), 1, "폴더를 읽지 못하면 행을 지우지 않는다");
        assert!(sh.snapshot().skipped_errors > 0);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn extension_filter_limits_rows_and_lists_files() {
        let dir = tmp("ext");
        let src = dir.join("src");
        fs::create_dir_all(src.join("sub")).unwrap();
        fs::write(src.join("a.HWPX"), b"1").unwrap();
        fs::write(src.join("b.exe"), b"2").unwrap();
        fs::write(src.join("noext"), b"3").unwrap();
        fs::write(src.join("sub").join("c.txt"), b"4").unwrap();
        let mut c = db(&dir);
        let root = src.to_string_lossy().into_owned();
        let exts = vec![".hwpx".to_string(), ".txt".to_string()];
        let sh = Shared::new();
        run_scan_filtered(&mut c, 1, &root, &sh, true, &exts);
        assert_eq!((sh.snapshot().total, sh.snapshot().added), (2, 2));
        let rows = list_files(&c, 1, Some(&root), 0, 100).unwrap();
        assert_eq!(rows.len(), 2);
        assert!(rows[0].0 < rows[1].0, "경로순");
        assert_eq!(list_files(&c, 1, None, 1, 100).unwrap().len(), 1, "offset");
        assert_eq!(list_files(&c, 1, Some("/없는루트"), 0, 100).unwrap().len(), 0);
        let _ = fs::remove_dir_all(&dir);
    }
}
