//! Windows 내장 SQLite(`winsqlite3.dll`, System32)를 실행 중 불러 쓴다.
//! 실행 파일에 SQLite를 넣지 않아 크기가 늘지 않고 C 컴파일러도 필요 없다.

use std::ffi::{CStr, c_char, c_int, c_void};
use std::sync::OnceLock;

use windows_sys::Win32::System::LibraryLoader::{GetProcAddress, LOAD_LIBRARY_SEARCH_SYSTEM32, LoadLibraryExW};

type Db = *mut c_void;
type Stmt = *mut c_void;

const SQLITE_OK: c_int = 0;
const SQLITE_ROW: c_int = 100;
const SQLITE_DONE: c_int = 101;
const SQLITE_OPEN_READWRITE: c_int = 0x2;
const SQLITE_OPEN_CREATE: c_int = 0x4;
const SQLITE_OPEN_FULLMUTEX: c_int = 0x10000;
const SQLITE_TRANSIENT: isize = -1;

#[allow(clippy::type_complexity)]
struct Lib {
    open_v2: extern "system" fn(*const c_char, *mut Db, c_int, *const c_char) -> c_int,
    close_v2: extern "system" fn(Db) -> c_int,
    exec: extern "system" fn(Db, *const c_char, *const c_void, *const c_void, *mut *mut c_char) -> c_int,
    prepare_v2: extern "system" fn(Db, *const c_char, c_int, *mut Stmt, *mut *const c_char) -> c_int,
    bind_int64: extern "system" fn(Stmt, c_int, i64) -> c_int,
    bind_double: extern "system" fn(Stmt, c_int, f64) -> c_int,
    bind_text: extern "system" fn(Stmt, c_int, *const c_char, c_int, isize) -> c_int,
    bind_blob: extern "system" fn(Stmt, c_int, *const c_void, c_int, isize) -> c_int,
    step: extern "system" fn(Stmt) -> c_int,
    reset: extern "system" fn(Stmt) -> c_int,
    finalize: extern "system" fn(Stmt) -> c_int,
    column_int64: extern "system" fn(Stmt, c_int) -> i64,
    column_double: extern "system" fn(Stmt, c_int) -> f64,
    column_text: extern "system" fn(Stmt, c_int) -> *const u8,
    column_blob: extern "system" fn(Stmt, c_int) -> *const c_void,
    column_bytes: extern "system" fn(Stmt, c_int) -> c_int,
    errmsg: extern "system" fn(Db) -> *const c_char,
    last_insert_rowid: extern "system" fn(Db) -> i64,
    changes: extern "system" fn(Db) -> c_int,
    busy_timeout: extern "system" fn(Db, c_int) -> c_int,
}

static LIB: OnceLock<Option<Lib>> = OnceLock::new();

fn lib() -> Result<&'static Lib, String> {
    LIB.get_or_init(|| unsafe {
        let name: Vec<u16> = "winsqlite3.dll\0".encode_utf16().collect();
        let h = LoadLibraryExW(name.as_ptr(), std::ptr::null_mut(), LOAD_LIBRARY_SEARCH_SYSTEM32);
        if h.is_null() {
            return None;
        }
        macro_rules! f {
            ($n:literal) => {
                std::mem::transmute(GetProcAddress(h, concat!($n, "\0").as_ptr())?)
            };
        }
        Some(Lib {
            open_v2: f!("sqlite3_open_v2"),
            close_v2: f!("sqlite3_close_v2"),
            exec: f!("sqlite3_exec"),
            prepare_v2: f!("sqlite3_prepare_v2"),
            bind_int64: f!("sqlite3_bind_int64"),
            bind_double: f!("sqlite3_bind_double"),
            bind_text: f!("sqlite3_bind_text"),
            bind_blob: f!("sqlite3_bind_blob"),
            step: f!("sqlite3_step"),
            reset: f!("sqlite3_reset"),
            finalize: f!("sqlite3_finalize"),
            column_int64: f!("sqlite3_column_int64"),
            column_double: f!("sqlite3_column_double"),
            column_text: f!("sqlite3_column_text"),
            column_blob: f!("sqlite3_column_blob"),
            column_bytes: f!("sqlite3_column_bytes"),
            errmsg: f!("sqlite3_errmsg"),
            last_insert_rowid: f!("sqlite3_last_insert_rowid"),
            changes: f!("sqlite3_changes"),
            busy_timeout: f!("sqlite3_busy_timeout"),
        })
    })
    .as_ref()
    .ok_or_else(|| "winsqlite3.dll을 불러오지 못했습니다".to_string())
}

pub struct Connection {
    db: Db,
}

// 연결은 FULLMUTEX로 열고, 바깥에서도 Mutex로 감싸 한 번에 한 스레드만 쓴다.
unsafe impl Send for Connection {}

pub enum Arg<'a> {
    Int(i64),
    Real(f64),
    Text(&'a str),
    Blob(&'a [u8]),
}

pub struct Row {
    stmt: Stmt,
}

impl Row {
    pub fn int(&self, i: c_int) -> i64 {
        (lib().unwrap().column_int64)(self.stmt, i)
    }
    pub fn real(&self, i: c_int) -> f64 {
        (lib().unwrap().column_double)(self.stmt, i)
    }
    pub fn text(&self, i: c_int) -> String {
        let l = lib().unwrap();
        let p = (l.column_text)(self.stmt, i);
        let n = (l.column_bytes)(self.stmt, i);
        if p.is_null() || n <= 0 {
            return String::new();
        }
        String::from_utf8_lossy(unsafe { std::slice::from_raw_parts(p, n as usize) }).into_owned()
    }
    pub fn blob(&self, i: c_int) -> Vec<u8> {
        let l = lib().unwrap();
        let p = (l.column_blob)(self.stmt, i);
        let n = (l.column_bytes)(self.stmt, i);
        if p.is_null() || n <= 0 {
            return Vec::new();
        }
        unsafe { std::slice::from_raw_parts(p as *const u8, n as usize) }.to_vec()
    }
}

impl Connection {
    pub fn open(path: &str) -> Result<Connection, String> {
        let l = lib()?;
        let c = std::ffi::CString::new(path).map_err(|e| e.to_string())?;
        let mut db: Db = std::ptr::null_mut();
        let rc = (l.open_v2)(c.as_ptr(), &mut db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX,
                             std::ptr::null());
        let conn = Connection { db };
        if rc != SQLITE_OK {
            return Err(conn.error());
        }
        (l.busy_timeout)(db, 2000);
        Ok(conn)
    }

    fn error(&self) -> String {
        let p = (lib().unwrap().errmsg)(self.db);
        if p.is_null() { "sqlite".into() } else { unsafe { CStr::from_ptr(p) }.to_string_lossy().into_owned() }
    }

    pub fn exec(&self, sql: &str) -> Result<(), String> {
        let c = std::ffi::CString::new(sql).map_err(|e| e.to_string())?;
        let rc = (lib()?.exec)(self.db, c.as_ptr(), std::ptr::null(), std::ptr::null(), std::ptr::null_mut());
        if rc == SQLITE_OK { Ok(()) } else { Err(self.error()) }
    }

    /// 문장을 실행하고 행마다 f를 부른다. 바뀐 행 수를 돌려준다.
    pub fn query(&self, sql: &str, args: &[Arg], mut f: impl FnMut(&Row)) -> Result<usize, String> {
        let l = lib()?;
        let mut stmt: Stmt = std::ptr::null_mut();
        let rc = (l.prepare_v2)(self.db, sql.as_ptr() as *const c_char, sql.len() as c_int, &mut stmt,
                                std::ptr::null_mut());
        if rc != SQLITE_OK {
            return Err(self.error());
        }
        let result = (|| {
            for (i, arg) in args.iter().enumerate() {
                let i = i as c_int + 1;
                let rc = match arg {
                    Arg::Int(v) => (l.bind_int64)(stmt, i, *v),
                    Arg::Real(v) => (l.bind_double)(stmt, i, *v),
                    Arg::Text(s) => (l.bind_text)(stmt, i, s.as_ptr() as *const c_char, s.len() as c_int,
                                                  SQLITE_TRANSIENT),
                    Arg::Blob(b) => (l.bind_blob)(stmt, i, b.as_ptr() as *const c_void, b.len() as c_int,
                                                  SQLITE_TRANSIENT),
                };
                if rc != SQLITE_OK {
                    return Err(self.error());
                }
            }
            loop {
                match (l.step)(stmt) {
                    SQLITE_ROW => f(&Row { stmt }),
                    SQLITE_DONE => return Ok((l.changes)(self.db) as usize),
                    _ => return Err(self.error()),
                }
            }
        })();
        (l.reset)(stmt);
        (l.finalize)(stmt);
        result
    }

    pub fn run(&self, sql: &str, args: &[Arg]) -> Result<usize, String> {
        self.query(sql, args, |_| {})
    }

    pub fn last_id(&self) -> i64 {
        (lib().unwrap().last_insert_rowid)(self.db)
    }
}

impl Drop for Connection {
    fn drop(&mut self) {
        if let Ok(l) = lib() {
            (l.close_v2)(self.db);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic() {
        let c = Connection::open(":memory:").unwrap();
        c.exec("CREATE TABLE t(a INTEGER, b TEXT, c BLOB, d REAL)").unwrap();
        c.run("INSERT INTO t VALUES(?,?,?,?)", &[Arg::Int(7), Arg::Text("한글"), Arg::Blob(&[0, 1, 2]), Arg::Real(1.5)])
            .unwrap();
        assert_eq!(c.last_id(), 1);
        let mut got = None;
        c.query("SELECT a,b,c,d FROM t", &[], |r| got = Some((r.int(0), r.text(1), r.blob(2), r.real(3)))).unwrap();
        assert_eq!(got, Some((7, "한글".to_string(), vec![0, 1, 2], 1.5)));
        assert!(c.exec("SELEC").is_err());
    }
}
