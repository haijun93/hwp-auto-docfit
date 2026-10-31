//! 타임머신 색인(timeline.db) — 앱의 docfit_core/timemachine과 같은 스키마·규칙.
//! 파일 내용은 읽지 않고 이름·종류·크기·생성/수정 시각만 기록한다. 쓰기는 에이전트 한 곳에서만.

use std::collections::{HashMap, HashSet};

use windows_sys::Win32::Foundation::FILETIME;
use windows_sys::Win32::Storage::FileSystem::{
    FIND_FIRST_EX_LARGE_FETCH, FindClose, FindExInfoBasic, FindExSearchNameMatch, FindFirstFileExW, FindNextFileW,
    GetFileAttributesExW, GetFileExInfoStandard, WIN32_FILE_ATTRIBUTE_DATA, WIN32_FIND_DATAW,
};

use crate::sqlite::{Arg, Connection};
use crate::util::wide;

const SCHEMA: &str = "
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, path TEXT NOT NULL, root TEXT NOT NULL, name TEXT NOT NULL,
    kind TEXT NOT NULL, size INTEGER NOT NULL, mtime REAL NOT NULL, ctime REAL NOT NULL, work_time REAL NOT NULL,
    flags TEXT NOT NULL DEFAULT '', cloud INTEGER NOT NULL DEFAULT 0, hidden INTEGER NOT NULL DEFAULT 0,
    seen INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS files_work_time ON files(work_time);
CREATE INDEX IF NOT EXISTS files_root ON files(root);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);";

const KINDS: &[(&str, &[&str])] = &[
    ("hwp", &["hwp", "hwpx", "hwt"]),
    ("doc", &["doc", "docx", "txt", "md"]),
    ("sheet", &["xls", "xlsx", "xlsm", "csv"]),
    ("slide", &["ppt", "pptx"]),
    ("pdf", &["pdf"]),
    ("image", &["jpg", "jpeg", "png", "gif", "bmp", "tif", "tiff", "webp"]),
];
const EXCLUDED_DIRS: &[&str] = &[
    "windows", "program files", "program files (x86)", "programdata", "$recycle.bin", "system volume information",
    "appdata", "temp", "packages", "user data", "cache", "code cache", "gpucache", "node_modules", ".git", ".venv",
    "venv", "__pycache__", ".dart_tool", ".gradle", ".idea", ".vscode",
];
const EXCLUDED_NAMES: &[&str] = &[
    "~$*", "~wrl*.tmp", "*.tmp", "*.crdownload", "*.part", "thumbs.db", "desktop.ini", "*.asv", "*.bak", "*.hwp.tmp",
    ".~lock.*", "*(무결성검사).json", ".rename-tmp-*",
];
const HIDDEN: u32 = 0x2 | 0x4;
const DIRECTORY: u32 = 0x10;
const REPARSE: u32 = 0x400;
const RECALL: u32 = 0x0040_0000 | 0x0004_0000 | 0x0000_1000;
const COPY_SLACK: f64 = 2.0;

/// 파이썬 path_key와 같게: 구분자를 \로, 소문자.
pub fn path_key(path: &str) -> String {
    path.replace('/', "\\").trim_end_matches('\\').to_lowercase()
}

pub fn kind_of(name: &str) -> Option<&'static str> {
    let ext = name.rsplit_once('.')?.1.to_lowercase();
    KINDS.iter().find(|(_, exts)| exts.contains(&ext.as_str())).map(|(k, _)| *k)
}

/// '*'만 쓰는 간단한 글롭(대소문자는 호출 쪽에서 맞춘다).
fn glob(pattern: &str, text: &str) -> bool {
    let parts: Vec<&str> = pattern.split('*').collect();
    if parts.len() == 1 {
        return pattern == text;
    }
    let mut rest = text;
    for (i, part) in parts.iter().enumerate() {
        if i == 0 {
            let Some(r) = rest.strip_prefix(part) else { return false };
            rest = r;
        } else if i == parts.len() - 1 {
            return rest.ends_with(part);
        } else if let Some(pos) = rest.find(part) {
            rest = &rest[pos + part.len()..];
        } else {
            return false;
        }
    }
    true
}

pub fn skip_dir(name: &str, attributes: u32) -> bool {
    let lower = name.to_lowercase();
    EXCLUDED_DIRS.contains(&lower.as_str()) || attributes & (HIDDEN | REPARSE) != 0 || name.starts_with('.')
}

pub fn skip_file(name: &str, attributes: u32) -> bool {
    if kind_of(name).is_none() || attributes & HIDDEN != 0 {
        return true;
    }
    let lower = name.to_lowercase();
    EXCLUDED_NAMES.iter().any(|p| glob(p, &lower))
}

/// 파이썬 st_mtime과 같은 값: 초 + 나노초 × 1e-9.
fn unix(ft: FILETIME) -> f64 {
    let ticks = ((ft.dwHighDateTime as i64) << 32 | ft.dwLowDateTime as i64) - 116_444_736_000_000_000;
    let ns = ticks * 100;
    ns.div_euclid(1_000_000_000) as f64 + ns.rem_euclid(1_000_000_000) as f64 * 1e-9
}

pub fn work_time(ctime: f64, mtime: f64, mtime_only: bool) -> (f64, &'static str) {
    let flags = if ctime > mtime + COPY_SLACK {
        "copied"
    } else if (ctime - mtime).abs() <= COPY_SLACK {
        "new"
    } else {
        ""
    };
    (if mtime_only { mtime } else { ctime.max(mtime) }, flags)
}

struct Row {
    path: String,
    name: String,
    kind: &'static str,
    size: i64,
    mtime: f64,
    ctime: f64,
    cloud: bool,
}

pub struct Timeline {
    conn: Connection,
    pub mtime_only: bool,
}

#[derive(Default, Debug)]
pub struct ScanResult {
    pub seen: usize,
    pub written: usize,
    pub removed: usize,
}

impl Timeline {
    pub fn open(path: &str) -> Result<Timeline, String> {
        let conn = Connection::open(path)?;
        conn.exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-1000;")?;
        conn.exec(SCHEMA)?;
        Ok(Timeline { conn, mtime_only: false })
    }

    fn upsert(&self, root: &str, rows: &[Row]) -> Result<usize, String> {
        if rows.is_empty() {
            return Ok(0);
        }
        self.conn.exec("BEGIN")?;
        let root_key = path_key(root);
        for r in rows {
            let (wt, flags) = work_time(r.ctime, r.mtime, self.mtime_only);
            let result = self.conn.run(
                "INSERT INTO files(key, path, root, name, kind, size, mtime, ctime, work_time, flags, cloud) \
                 VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET path=excluded.path, name=excluded.name, \
                 kind=excluded.kind, size=excluded.size, mtime=excluded.mtime, ctime=excluded.ctime, \
                 work_time=excluded.work_time, flags=excluded.flags, cloud=excluded.cloud",
                &[Arg::Text(&path_key(&r.path)), Arg::Text(&r.path), Arg::Text(&root_key), Arg::Text(&r.name),
                  Arg::Text(r.kind), Arg::Int(r.size), Arg::Real(r.mtime), Arg::Real(r.ctime), Arg::Real(wt),
                  Arg::Text(flags), Arg::Int(r.cloud as i64)],
            );
            if let Err(e) = result {
                let _ = self.conn.exec("ROLLBACK");
                return Err(e);
            }
        }
        self.conn.exec("COMMIT")?;
        Ok(rows.len())
    }

    fn known(&self, root: &str) -> Result<HashMap<String, (i64, f64, f64)>, String> {
        let mut map = HashMap::new();
        self.conn.query("SELECT key, size, mtime, ctime FROM files WHERE root = ?", &[Arg::Text(&path_key(root))],
                        |r| {
                            map.insert(r.text(0), (r.int(1), r.real(2), r.real(3)));
                        })?;
        Ok(map)
    }

    /// 조사 폴더 전체 증분 갱신(변경 없는 파일은 쓰지 않음, 사라진 파일 정리).
    pub fn scan_root(&self, root: &str) -> Result<ScanResult, String> {
        let known = self.known(root)?;
        let mut seen = HashSet::new();
        let mut pending = Vec::new();
        let mut result = ScanResult::default();
        let mut stack = vec![root.trim_end_matches('\\').to_string()];
        while let Some(folder) = stack.pop() {
            walk_dir(&folder, |name, attributes, size, mtime, ctime| {
                let path = format!("{folder}\\{name}");
                if attributes & DIRECTORY != 0 {
                    if !skip_dir(name, attributes) {
                        stack.push(path);
                    }
                    return;
                }
                if skip_file(name, attributes) {
                    return;
                }
                let key = path_key(&path);
                result.seen += 1;
                if known.get(&key) != Some(&(size, mtime, ctime)) {
                    pending.push(Row { name: name.to_string(), kind: kind_of(name).unwrap_or("other"), size, mtime,
                                       ctime, cloud: attributes & RECALL != 0, path });
                }
                seen.insert(key);
            });
            if pending.len() >= 500 {
                result.written += self.upsert(root, &pending)?;
                pending.clear();
            }
        }
        result.written += self.upsert(root, &pending)?;
        let gone: Vec<&String> = known.keys().filter(|k| !seen.contains(*k)).collect();
        if !gone.is_empty() {
            self.conn.exec("BEGIN")?;
            for key in &gone {
                self.conn.run("DELETE FROM files WHERE key = ?", &[Arg::Text(key)])?;
            }
            self.conn.exec("COMMIT")?;
        }
        result.removed = gone.len();
        Ok(result)
    }

    /// 감시 알림 한 건: 지금 실제 상태를 보고 반영한다(폴더면 그 아래를 훑는다).
    pub fn apply(&self, root: &str, relative: &str) -> Result<(), String> {
        let parts = safe_relative_path(relative).ok_or_else(|| "잘못된 상대 경로".to_string())?;
        let path = format!("{}\\{}", root.trim_end_matches('\\'), relative);
        // 경로 중간에 제외 폴더가 있으면 무시.
        if parts[..parts.len().saturating_sub(1)].iter().any(|p| skip_dir(p, 0)) {
            return Ok(());
        }
        let mut info: WIN32_FILE_ATTRIBUTE_DATA = unsafe { std::mem::zeroed() };
        let exists = unsafe { GetFileAttributesExW(wide(&path).as_ptr(), GetFileExInfoStandard, &mut info as *mut _ as _) } != 0;
        let key = path_key(&path);
        if !exists {
            self.conn.run("DELETE FROM files WHERE key = ? OR (key > ? AND key < ?)",
                          &[Arg::Text(&key), Arg::Text(&format!("{key}\\")), Arg::Text(&format!("{key}]"))])?;
            return Ok(());
        }
        let name = parts.last().copied().unwrap_or("");
        if info.dwFileAttributes & DIRECTORY != 0 {
            if skip_dir(name, info.dwFileAttributes) {
                return Ok(());
            }
            // 새로 생기거나 이름이 바뀐 폴더: 그 아래만 훑어 넣는다.
            let mut rows = Vec::new();
            let mut stack = vec![path];
            while let Some(folder) = stack.pop() {
                walk_dir(&folder, |n, a, size, mtime, ctime| {
                    let p = format!("{folder}\\{n}");
                    if a & DIRECTORY != 0 {
                        if !skip_dir(n, a) {
                            stack.push(p);
                        }
                    } else if !skip_file(n, a) {
                        rows.push(Row { name: n.to_string(), kind: kind_of(n).unwrap_or("other"), size, mtime, ctime,
                                        cloud: a & RECALL != 0, path: p });
                    }
                });
            }
            self.upsert(root, &rows)?;
            return Ok(());
        }
        if skip_file(name, info.dwFileAttributes) {
            return Ok(());
        }
        let size = ((info.nFileSizeHigh as i64) << 32) | info.nFileSizeLow as i64;
        self.upsert(root, &[Row { name: name.to_string(), kind: kind_of(name).unwrap_or("other"), size,
                                  mtime: unix(info.ftLastWriteTime), ctime: unix(info.ftCreationTime),
                                  cloud: info.dwFileAttributes & RECALL != 0, path }])?;
        Ok(())
    }

    pub fn drop_other_roots(&self, roots: &[String]) -> Result<usize, String> {
        let keep: Vec<String> = roots.iter().map(|r| path_key(r)).collect();
        let mut stale = Vec::new();
        self.conn.query("SELECT DISTINCT root FROM files", &[], |r| {
            let root = r.text(0);
            if !keep.contains(&root) {
                stale.push(root);
            }
        })?;
        let mut n = 0;
        for root in stale {
            n += self.conn.run("DELETE FROM files WHERE root = ?", &[Arg::Text(&root)])?;
        }
        Ok(n)
    }

    pub fn count(&self) -> i64 {
        let mut n = 0;
        let _ = self.conn.query("SELECT COUNT(*) FROM files WHERE hidden = 0", &[], |r| n = r.int(0));
        n
    }
}

/// 한 폴더의 항목(이름·속성·크기·수정·생성 시각). FindFirstFileEx 큰 가져오기로 파일마다 추가 호출이 없다.
fn walk_dir(folder: &str, mut f: impl FnMut(&str, u32, i64, f64, f64)) {
    let pattern = wide(&format!("{folder}\\*"));
    let mut data: WIN32_FIND_DATAW = unsafe { std::mem::zeroed() };
    let h = unsafe {
        FindFirstFileExW(pattern.as_ptr(), FindExInfoBasic, &mut data as *mut _ as _, FindExSearchNameMatch,
                         std::ptr::null(), FIND_FIRST_EX_LARGE_FETCH)
    };
    if h == windows_sys::Win32::Foundation::INVALID_HANDLE_VALUE {
        return;
    }
    loop {
        let len = data.cFileName.iter().position(|&c| c == 0).unwrap_or(data.cFileName.len());
        let name = String::from_utf16_lossy(&data.cFileName[..len]);
        if name != "." && name != ".." {
            let size = ((data.nFileSizeHigh as i64) << 32) | data.nFileSizeLow as i64;
            f(&name, data.dwFileAttributes, size, unix(data.ftLastWriteTime), unix(data.ftCreationTime));
        }
        if unsafe { FindNextFileW(h, &mut data) } == 0 {
            break;
        }
    }
    unsafe { FindClose(h) };
}

pub fn safe_relative_path(relative: &str) -> Option<Vec<&str>> {
    if relative.is_empty() {
        return None;
    }
    // Unix 스타일 슬래시나 혼용 거부
    if relative.contains('/') {
        return None;
    }
    // 드라이브 문자(예: C:) 및 ADS(stream) 콜론 전체 거부
    if relative.contains(':') {
        return None;
    }
    // 물음표(와일드카드 및 \\?\ 장치 경로 접두어) 거부
    if relative.contains('?') {
        return None;
    }
    // UNC 또는 선행/후행 백슬래시 거부
    if relative.starts_with('\\') || relative.ends_with('\\') {
        return None;
    }
    let parts: Vec<&str> = relative.split('\\').collect();
    if parts.is_empty() {
        return None;
    }
    for &p in &parts {
        if p.is_empty() || p == "." || p == ".." {
            return None;
        }
        // Win32 경로 정규화 취약점 방지: 끝 공백이나 마침표 거부
        if p.ends_with(' ') || p.ends_with('.') {
            return None;
        }
        // 선행 공백이나 공백만 있는 세그먼트 거부
        if p.starts_with(' ') || p.trim().is_empty() {
            return None;
        }
        // DOS 예약 장치명 거부 (확장자 유무 불문)
        let stem = p.split('.').next().unwrap_or(p);
        let upper = stem.to_ascii_uppercase();
        let is_device = matches!(
            upper.as_str(),
            "CON" | "PRN" | "AUX" | "NUL"
                | "COM1" | "COM2" | "COM3" | "COM4" | "COM5" | "COM6" | "COM7" | "COM8" | "COM9"
                | "LPT1" | "LPT2" | "LPT3" | "LPT4" | "LPT5" | "LPT6" | "LPT7" | "LPT8" | "LPT9"
        );
        if is_device {
            return None;
        }
    }
    Some(parts)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rules_match_python() {
        assert!(!skip_file("보고서.HWPX", 0));
        for name in ["~$보고서.docx", "~WRL0001.tmp", "a.tmp", "Thumbs.db", "a.bak", "setup.exe", "a(무결성검사).json"] {
            assert!(skip_file(name, 0), "{name}");
        }
        assert!(skip_file("a.pdf", 2));
        assert!(skip_dir("AppData", 0) && skip_dir(".git", 0) && skip_dir("x", 0x400));
        assert!(!skip_dir("2026 업무", 0));
        assert_eq!(work_time(100.0, 500.0, false), (500.0, ""));
        assert_eq!(work_time(900.0, 500.0, false), (900.0, "copied"));
        assert_eq!(work_time(900.0, 500.0, true), (500.0, "copied"));
        assert_eq!(path_key("C:/Users/A/문서/"), "c:\\users\\a\\문서");
        assert!(glob("~wrl*.tmp", "~wrl0001.tmp") && !glob("~wrl*.tmp", "x~wrl.tmp"));
    }

    #[test]
    fn scan_and_apply() {
        let root = std::env::temp_dir().join(format!("kagent-tl-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&root);
        std::fs::create_dir_all(root.join("하위").join("node_modules")).unwrap();
        std::fs::write(root.join("보고서.hwpx"), b"x").unwrap();
        std::fs::write(root.join("하위").join("표.xlsx"), b"x").unwrap();
        std::fs::write(root.join("하위").join("node_modules").join("x.pdf"), b"x").unwrap();
        std::fs::write(root.join("~$임시.docx"), b"x").unwrap();
        let r = root.to_string_lossy().into_owned();
        let tl = Timeline::open(":memory:").unwrap();
        let first = tl.scan_root(&r).unwrap();
        assert_eq!((first.seen, first.written, first.removed), (2, 2, 0));
        let again = tl.scan_root(&r).unwrap();
        assert_eq!((again.seen, again.written), (2, 0));
        std::fs::write(root.join("새 문서.pdf"), b"y").unwrap();
        tl.apply(&r, "새 문서.pdf").unwrap();
        assert_eq!(tl.count(), 3);
        std::fs::remove_dir_all(root.join("하위")).unwrap();
        tl.apply(&r, "하위").unwrap();
        assert_eq!(tl.count(), 2);
        std::fs::create_dir_all(root.join("옮긴 폴더")).unwrap();
        std::fs::write(root.join("옮긴 폴더").join("a.docx"), b"z").unwrap();
        tl.apply(&r, "옮긴 폴더").unwrap();
        assert_eq!(tl.count(), 3);
        tl.apply(&r, "node_modules\\b.pdf").unwrap();
        assert_eq!(tl.count(), 3);
        assert_eq!(tl.drop_other_roots(&[]).unwrap(), 3);
        let _ = std::fs::remove_dir_all(&root);
    }

    #[test]
    fn apply_rejects_absolute_and_traversal_paths() {
        let base = std::env::temp_dir().join(format!("kagent-tl-traversal-{}", std::process::id()));
        let root = base.join("root");
        let outside = base.join("outside.pdf");
        let _ = std::fs::remove_dir_all(&base);
        std::fs::create_dir_all(&root).unwrap();
        std::fs::write(&outside, b"sentinel").unwrap();
        std::fs::write(root.join("valid.pdf"), b"valid").unwrap();

        let r = root.to_string_lossy().into_owned();
        let tl = Timeline::open(":memory:").unwrap();
        tl.scan_root(&r).unwrap();
        assert_eq!(tl.count(), 1);

        // 잘못된 경로 거부 검증
        assert!(tl.apply(&r, "..\\outside.pdf").is_err());
        assert!(tl.apply(&r, "C:\\outside.pdf").is_err());
        assert!(tl.apply(&r, "\\\\server\\share\\x.pdf").is_err());
        assert!(tl.apply(&r, "/absolute/x.pdf").is_err());
        assert!(tl.apply(&r, "\\leading\\x.pdf").is_err());
        assert!(tl.apply(&r, "trailing\\").is_err());
        assert!(tl.apply(&r, "sub\\\\empty_segment.pdf").is_err());
        assert!(tl.apply(&r, ".").is_err());
        assert!(tl.apply(&r, "..").is_err());
        assert!(tl.apply(&r, "").is_err());

        // Win32 정규화 alias, 장치명, ADS, 와일드카드 거부 검증
        assert!(tl.apply(&r, "sub\\file.txt.").is_err());
        assert!(tl.apply(&r, "sub\\file.txt ").is_err());
        assert!(tl.apply(&r, "sub\\ CON").is_err());
        assert!(tl.apply(&r, "sub\\CON").is_err());
        assert!(tl.apply(&r, "sub\\con.txt").is_err());
        assert!(tl.apply(&r, "sub\\NUL").is_err());
        assert!(tl.apply(&r, "sub\\prn.pdf").is_err());
        assert!(tl.apply(&r, "sub\\COM1").is_err());
        assert!(tl.apply(&r, "file.pdf:stream").is_err());
        assert!(tl.apply(&r, "\\\\?\\C:\\outside.pdf").is_err());
        assert!(tl.apply(&r, "sub\\?file.txt").is_err());

        // sentinel 파일 및 DB count 불변 확인
        assert_eq!(tl.count(), 1);
        assert_eq!(std::fs::read(&outside).unwrap(), b"sentinel");

        // 정상 하위 경로는 적용
        std::fs::create_dir_all(root.join("sub")).unwrap();
        std::fs::write(root.join("sub").join("nested.pdf"), b"nested").unwrap();
        assert!(tl.apply(&r, "sub\\nested.pdf").is_ok());
        assert_eq!(tl.count(), 2);

        let _ = std::fs::remove_dir_all(&base);
    }
}
