//! 몽땅클립보드 저장소(clip.db)와 설정(settings.json).
//!
//! - 내용(payload)과 미리보기는 DPAPI로 암호화해 저장한다.
//! - 같은 내용을 다시 복사하면 새로 쓰지 않고 순서만 앞으로 올린다(중복 0바이트).
//! - 한도: 고정하지 않은 항목 개수·전체 용량·보관 기간. 항목 하나의 상한은 기록 전에 막는다.

use std::cell::RefCell;
use std::collections::HashMap;

use crate::category::{self, Category, CategorySet, Entry};
use crate::crypt;
use crate::json::{self, Value};
use crate::sqlite::{Arg, Connection};

/// 스키마 버전(PRAGMA user_version). 앱(kagent_client.py)이 같은 값을 확인한다.
pub const SCHEMA_VERSION: i64 = 3;

#[derive(Clone, Debug)]
pub struct Settings {
    pub max_items: i64,
    pub max_item_bytes: i64,
    pub max_total_bytes: i64,
    pub max_age_days: f64,
    pub auto_paste: bool,
    /// 빠른 목록 창을 포커스를 잃어도 화면에 유지한다(스티커 메모 모드).
    pub sticky_popup: bool,
    /// 빠른 목록 창을 다른 창보다 위에 둔다.
    pub always_on_top: bool,
    pub paused: bool,
    pub hotkey: String,
    pub excluded_apps: Vec<String>,
    /// 스크린샷 폴더(Win+PrtScn·캡처 도구 자동 저장)에 새로 생긴 PNG도 기록.
    pub watch_screenshots: bool,
    /// 타임머신 조사 폴더(앱이 정해 준다, 비어 있으면 감시 안 함).
    pub timeline_roots: Vec<String>,
    pub timeline_mtime_only: bool,
    /// 빠른 목록 창의 마지막 논리 화면 좌표·크기.
    pub popup_x: i64,
    pub popup_y: i64,
    pub popup_width: i64,
    pub popup_height: i64,
    /// 스티커 창 접힘 상태.
    pub popup_collapsed: bool,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            max_items: 50,
            max_item_bytes: 10 * 1024 * 1024,
            max_total_bytes: 200 * 1024 * 1024,
            max_age_days: 30.0,
            auto_paste: true,
            sticky_popup: false,
            always_on_top: true,
            paused: false,
            hotkey: "Ctrl+Shift+V".into(),
            // 암호 관리자는 제외 신호를 보내지만, 보내지 않는 프로그램도 있어 기본으로 뺀다.
            excluded_apps: ["keepass.exe", "keepassxc.exe", "1password.exe", "bitwarden.exe", "lastpass.exe"]
                .iter()
                .map(|s| s.to_string())
                .collect(),
            watch_screenshots: true,
            timeline_roots: Vec::new(),
            timeline_mtime_only: false,
            popup_x: -1,
            popup_y: -1,
            popup_width: 0,
            popup_height: 0,
            popup_collapsed: false,
        }
    }
}

fn string_list(v: &Value, key: &str, lower: bool, max_len: usize) -> Option<Vec<String>> {
    let Some(Value::Arr(items)) = v.get(key) else { return None };
    Some(items
        .iter()
        .filter_map(|i| if let Value::Str(s) = i { Some(if lower { s.to_lowercase() } else { s.clone() }) } else { None })
        .filter(|s| !s.is_empty() && s.len() <= max_len)
        .take(100)
        .collect())
}

impl Settings {
    pub fn to_json(&self) -> Value {
        Value::obj(vec![
            ("max_items", self.max_items.into()),
            ("max_item_mb", (self.max_item_bytes / 1024 / 1024).into()),
            ("max_total_mb", (self.max_total_bytes / 1024 / 1024).into()),
            ("max_age_days", self.max_age_days.into()),
            ("auto_paste", self.auto_paste.into()),
            ("sticky_popup", self.sticky_popup.into()),
            ("always_on_top", self.always_on_top.into()),
            ("paused", self.paused.into()),
            ("hotkey", self.hotkey.as_str().into()),
            ("excluded_apps", Value::Arr(self.excluded_apps.iter().map(|s| s.as_str().into()).collect())),
            ("watch_screenshots", self.watch_screenshots.into()),
            ("timeline_roots", Value::Arr(self.timeline_roots.iter().map(|s| s.as_str().into()).collect())),
            ("timeline_mtime_only", self.timeline_mtime_only.into()),
            ("popup_x", self.popup_x.into()),
            ("popup_y", self.popup_y.into()),
            ("popup_width", self.popup_width.into()),
            ("popup_height", self.popup_height.into()),
            ("popup_collapsed", self.popup_collapsed.into()),
        ])
    }

    /// 값이 있고 범위 안이면 반영한다(잘못된 값은 무시).
    pub fn apply(&mut self, v: &Value) {
        if let Some(n) = v.num("max_items").filter(|n| (10.0..=1000.0).contains(n)) {
            self.max_items = n as i64;
        }
        if let Some(n) = v.num("max_item_mb").filter(|n| (1.0..=50.0).contains(n)) {
            self.max_item_bytes = n as i64 * 1024 * 1024;
        }
        if let Some(n) = v.num("max_total_mb").filter(|n| (10.0..=2000.0).contains(n)) {
            self.max_total_bytes = n as i64 * 1024 * 1024;
        }
        if let Some(n) = v.num("max_age_days").filter(|n| (1.0..=3650.0).contains(n)) {
            self.max_age_days = n;
        }
        if let Some(b) = v.bool("auto_paste") {
            self.auto_paste = b;
        }
        if let Some(b) = v.bool("sticky_popup") {
            self.sticky_popup = b;
        }
        if let Some(b) = v.bool("always_on_top") {
            self.always_on_top = b;
        }
        if let Some(b) = v.bool("paused") {
            self.paused = b;
        }
        if let Some(s) = v.str("hotkey").filter(|s| s.len() <= 40) {
            self.hotkey = s.to_string();
        }
        if let Some(list) = string_list(v, "excluded_apps", true, 100) {
            self.excluded_apps = list;
        }
        if let Some(b) = v.bool("watch_screenshots") {
            self.watch_screenshots = b;
        }
        // 조사 폴더: 절대 경로(드라이브 문자)만, 최대 20개.
        if let Some(list) = string_list(v, "timeline_roots", false, 1000) {
            self.timeline_roots = list
                .into_iter()
                .filter(|p| p.len() > 3 && p.as_bytes()[1] == b':' && !p.contains("..") &&
                    !p.starts_with("\\\\") && !p.split(|ch| ch == '\\' || ch == '/')
                        .any(|part| part.eq_ignore_ascii_case("$Recycle.Bin")))
                .take(20)
                .collect();
        }
        if let Some(b) = v.bool("timeline_mtime_only") {
            self.timeline_mtime_only = b;
        }
        if let Some(n) = v.num("popup_x").filter(|n| (-100_000.0..=100_000.0).contains(n)) { self.popup_x = n as i64; }
        if let Some(n) = v.num("popup_y").filter(|n| (-100_000.0..=100_000.0).contains(n)) { self.popup_y = n as i64; }
        if let Some(n) = v.num("popup_width").filter(|n| (200.0..=4000.0).contains(n)) { self.popup_width = n as i64; }
        if let Some(n) = v.num("popup_height").filter(|n| (150.0..=4000.0).contains(n)) { self.popup_height = n as i64; }
        if let Some(b) = v.bool("popup_collapsed") { self.popup_collapsed = b; }
    }

    pub fn load(path: &str) -> Settings {
        let mut s = Settings::default();
        if let Some(v) = std::fs::read_to_string(path).ok().and_then(|t| json::parse(&t)) {
            s.apply(&v);
        }
        s
    }

    pub fn save(&self, path: &str) -> std::io::Result<()> {
        let temp = format!("{path}.tmp");
        std::fs::write(&temp, json::to_string(&self.to_json()))?;
        std::fs::rename(&temp, path)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Summary {
    pub id: i64,
    pub kind: String,
    pub preview: String,
    pub pinned: bool,
    pub used: f64,
    pub size: i64,
    /// 빠른 목록 분류(전체·문서·그림·파일·폴더·웹·화면캡처, 겹칠 수 있음). 목록을 읽을 때 한 번 계산해 둔다.
    pub cats: CategorySet,
}

/// 분류·검색용 항목 정보(복호화 결과에서 만든 것, id별 캐시).
#[derive(Clone, Debug, Default)]
struct Info {
    cats: CategorySet,
    paths: Vec<String>,
    web_url: Option<String>,
}

/// 파일 항목 경로가 폴더인지. 네트워크 경로는 조회가 오래 걸릴 수 있어 확장자 추정(None)에 맡긴다.
fn path_kind(path: &str) -> Option<bool> {
    if path.starts_with("\\\\") {
        return None;
    }
    std::fs::metadata(path).ok().map(|m| m.is_dir())
}

impl Summary {
    pub fn to_json(&self) -> Value {
        Value::obj(vec![
            ("id", self.id.into()),
            ("kind", self.kind.as_str().into()),
            ("preview", self.preview.as_str().into()),
            ("pinned", self.pinned.into()),
            ("used", self.used.into()),
            ("size", self.size.into()),
        ])
    }
}

pub struct Store {
    conn: Connection,
    /// 복호화한 미리보기(id → 글). 항목이 바뀔 때마다 50개를 다시 풀지 않도록 둔다.
    previews: HashMap<i64, String>,
    /// 분류·검색 정보(id → Info). 같은 내용을 다시 복사해 서식이 바뀌면 지운다.
    info: RefCell<HashMap<i64, Info>>,
}

/// FNV-1a 64비트(중복 판단용 — 길이와 종류를 함께 키로 쓴다).
pub fn content_hash(kind: &str, data: &[u8]) -> String {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in kind.as_bytes().iter().chain(data) {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    format!("{kind}:{}:{h:016x}", data.len())
}

impl Store {
    pub fn open(path: &str) -> Result<Store, String> {
        let conn = Connection::open(path)?;
        conn.exec(
            "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-512;
             CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY, created REAL NOT NULL, used REAL NOT NULL, kind TEXT NOT NULL,
                hash TEXT NOT NULL UNIQUE, size INTEGER NOT NULL, pinned INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT '', preview BLOB NOT NULL, payload BLOB NOT NULL,
                extra BLOB NOT NULL DEFAULT x'');
             CREATE INDEX IF NOT EXISTS items_used ON items(used);",
        )?;
        // v1 → v2: HTML·RTF, v2 → v3: 전체 형식 묶음은 같은 extra 칸을 사용.
        let mut version = 0;
        conn.query("PRAGMA user_version", &[], |r| version = r.int(0))?;
        if version < 2 {
            let _ = conn.exec("ALTER TABLE items ADD COLUMN extra BLOB NOT NULL DEFAULT x''");
        }
        if version < 3 { conn.exec(&format!("PRAGMA user_version={SCHEMA_VERSION}"))?; }
        Ok(Store { conn, previews: HashMap::new(), info: RefCell::new(HashMap::new()) })
    }

    /// 새 항목이면 (id, true), 이미 있던 내용이면 (id, false)(순서만 앞으로, 서식은 새것으로).
    /// extra: 같은 내용의 다른 형식(HTML·RTF) 묶음 — 중복 판단에는 쓰지 않는다.
    pub fn insert(&self, kind: &str, data: &[u8], extra: &[u8], preview: &str, source: &str, now: f64)
                  -> Result<(i64, bool), String> {
        let hash = content_hash(kind, data);
        let mut existing = None;
        self.conn.query("SELECT id FROM items WHERE hash = ?", &[Arg::Text(&hash)], |r| existing = Some(r.int(0)))?;
        let sealed_extra = if extra.is_empty() { Vec::new() } else { crypt::protect(extra).ok_or("암호화 실패")? };
        if let Some(id) = existing {
            if extra.is_empty() {
                self.conn.run("UPDATE items SET used = ? WHERE id = ?", &[Arg::Real(now), Arg::Int(id)])?;
            } else {
                self.conn.run("UPDATE items SET used = ?, extra = ? WHERE id = ?",
                              &[Arg::Real(now), Arg::Blob(&sealed_extra), Arg::Int(id)])?;
                self.info.borrow_mut().remove(&id);
            }
            return Ok((id, false));
        }
        let sealed = crypt::protect(data).ok_or("암호화 실패")?;
        let sealed_preview = crypt::protect(preview.as_bytes()).ok_or("암호화 실패")?;
        self.conn.run(
            "INSERT INTO items(created, used, kind, hash, size, source, preview, payload, extra)              VALUES(?,?,?,?,?,?,?,?,?)",
            &[Arg::Real(now), Arg::Real(now), Arg::Text(kind), Arg::Text(&hash),
              Arg::Int((data.len() + extra.len()) as i64), Arg::Text(source), Arg::Blob(&sealed_preview),
              Arg::Blob(&sealed), Arg::Blob(&sealed_extra)],
        )?;
        Ok((self.conn.last_id(), true))
    }

    /// 한도 정리: 보관 기간 → 개수 → 전체 용량 순서. 고정 항목은 지우지 않는다. 지운 개수.
    pub fn enforce(&self, s: &Settings, now: f64) -> Result<usize, String> {
        let mut removed = self.conn.run("DELETE FROM items WHERE pinned = 0 AND used < ?",
                                        &[Arg::Real(now - s.max_age_days * 86400.0)])?;
        removed += self.conn.run(
            "DELETE FROM items WHERE pinned = 0 AND id NOT IN \
             (SELECT id FROM items WHERE pinned = 0 ORDER BY used DESC LIMIT ?)",
            &[Arg::Int(s.max_items)],
        )?;
        loop {
            let total = self.total_bytes()?;
            if total <= s.max_total_bytes {
                break;
            }
            let n = self.conn.run(
                "DELETE FROM items WHERE id = (SELECT id FROM items WHERE pinned = 0 ORDER BY used ASC LIMIT 1)", &[])?;
            if n == 0 {
                break;
            }
            removed += n;
        }
        Ok(removed)
    }

    pub fn total_bytes(&self) -> Result<i64, String> {
        let mut total = 0;
        self.conn.query("SELECT COALESCE(SUM(size), 0) FROM items", &[], |r| total = r.int(0))?;
        Ok(total)
    }

    pub fn count(&self) -> Result<i64, String> {
        let mut n = 0;
        self.conn.query("SELECT COUNT(*) FROM items", &[], |r| n = r.int(0))?;
        Ok(n)
    }

    /// 최근 사용 순. query가 있으면 미리보기에서 대소문자 무시 부분 일치(복호화 뒤 비교).
    pub fn recent(&mut self, limit: usize, query: Option<&str>) -> Result<Vec<Summary>, String> {
        let needle = query.map(|q| q.to_lowercase()).filter(|q| !q.is_empty());
        self.collect(limit, |s, _| {
            needle.as_ref().is_none_or(|n| s.preview.to_lowercase().contains(n.as_str()))
        })
    }

    /// 빠른 목록용: 분류에 속하고 키워드(공백 낱말 모두, 한글 조합 중 글자 포함)가 들어 있는 항목을
    /// 최근 사용 순으로 limit개까지. 검색 대상은 미리보기·파일 전체 경로·웹 주소(`category::matches_query`).
    pub fn list(&mut self, limit: usize, cat: Category, query: &str) -> Result<Vec<Summary>, String> {
        let query = query.trim();
        self.collect(limit, |s, info| {
            s.cats.contains(cat)
                && (query.is_empty() || category::matches_query(&Entry {
                    preview: s.preview.clone(), paths: info.paths.clone(), web_url: info.web_url.clone(),
                    ..Default::default()
                }, query))
        })
    }

    /// 최근 사용 순으로 훑으며 keep을 통과한 항목을 모은다. 미리보기·분류는 처음 볼 때만 복호화해 캐시한다.
    /// limit개를 채우면 멈춘다(그 뒤 항목은 복호화하지 않는다).
    fn collect(&mut self, limit: usize, mut keep: impl FnMut(&Summary, &Info) -> bool)
               -> Result<Vec<Summary>, String> {
        struct Row { id: i64, kind: String, pinned: bool, used: f64, size: i64, source: String, sealed: Option<Vec<u8>> }
        let mut rows = Vec::new();
        let cached = &self.previews;
        self.conn.query("SELECT id, kind, preview, pinned, used, size, source FROM items ORDER BY used DESC", &[], |r| {
            let id = r.int(0);
            let sealed = (!cached.contains_key(&id)).then(|| r.blob(2));
            rows.push(Row { id, kind: r.text(1), pinned: r.int(3) != 0, used: r.real(4), size: r.int(5), source: r.text(6), sealed });
        })?;
        let mut out = Vec::new();
        for row in &rows {
            if out.len() >= limit {
                break;
            }
            let preview = match &row.sealed {
                Some(sealed) => {
                    let p = crypt::unprotect(sealed).map(|b| String::from_utf8_lossy(&b).into_owned()).unwrap_or_default();
                    self.previews.insert(row.id, p.clone());
                    p
                }
                None => self.previews.get(&row.id).cloned().unwrap_or_default(),
            };
            let cached_info = self.info.borrow().get(&row.id).cloned();
            let info = match cached_info {
                Some(info) => info,
                None => {
                    let info = self.compute_info(row.id, &row.kind, &row.source, &preview);
                    self.info.borrow_mut().insert(row.id, info.clone());
                    info
                }
            };
            let summary = Summary { id: row.id, kind: row.kind.clone(), preview, pinned: row.pinned, used: row.used,
                                    size: row.size, cats: info.cats };
            if keep(&summary, &info) {
                out.push(summary);
            }
        }
        let seen: std::collections::HashSet<i64> = rows.iter().map(|r| r.id).collect();
        self.previews.retain(|id, _| seen.contains(id));
        self.info.borrow_mut().retain(|id, _| seen.contains(id));
        Ok(out)
    }

    /// 분류 판별(category.rs 규칙): 글·파일 항목만 내용을 풀어 본다(그림은 출처·미리보기로 충분).
    fn compute_info(&self, id: i64, kind: &str, source: &str, preview: &str) -> Info {
        let mut entry = Entry { id, kind: kind.to_string(), preview: preview.to_string(), source: source.to_string(),
                                ..Default::default() };
        if kind == "files" {
            if let Ok(Some((_, data, _))) = self.payload(id) {
                entry.paths = String::from_utf8_lossy(&data).lines().map(str::trim).filter(|p| !p.is_empty())
                    .map(str::to_owned).collect();
            }
        } else if kind == "text" {
            let mut sealed: Option<(Vec<u8>, Vec<u8>)> = None;
            let _ = self.conn.query("SELECT payload, extra FROM items WHERE id = ?", &[Arg::Int(id)], |r| {
                sealed = Some((r.blob(0), r.blob(1)));
            });
            if let Some((payload, extra)) = sealed {
                // 본문은 주소 한 개인지 볼 때만 쓴다. 긴 글(암호문 8KB 초과)은 주소일 수 없으므로 풀지 않는다.
                if payload.len() <= 8192 {
                    if let Some(data) = crypt::unprotect(&payload) {
                        entry.text = String::from_utf8_lossy(&data).into_owned();
                    }
                }
                if !extra.is_empty() {
                    let extra = crypt::unprotect(&extra).unwrap_or_default();
                    entry.web_url = crate::open_item::web_url_from_extra(&extra);
                    entry.formats = crate::open_item::formats_from_extra(&extra).into_iter().map(|(n, _)| n).collect();
                }
            }
        }
        let cats = category::classify(&entry, &path_kind);
        Info { cats, paths: entry.paths, web_url: entry.web_url }
    }

    /// (종류, 내용, 서식 묶음).
    pub fn payload(&self, id: i64) -> Result<Option<(String, Vec<u8>, Vec<u8>)>, String> {
        let mut found = None;
        self.conn.query("SELECT kind, payload, extra FROM items WHERE id = ?", &[Arg::Int(id)], |r| {
            found = Some((r.text(0), r.blob(1), r.blob(2)))
        })?;
        Ok(match found {
            Some((kind, sealed, sealed_extra)) => {
                let extra = if sealed_extra.is_empty() { Vec::new() } else { crypt::unprotect(&sealed_extra).unwrap_or_default() };
                Some((kind, crypt::unprotect(&sealed).ok_or("복호화 실패")?, extra))
            }
            None => None,
        })
    }

    pub fn touch(&self, id: i64, now: f64) -> Result<bool, String> {
        Ok(self.conn.run("UPDATE items SET used = ? WHERE id = ?", &[Arg::Real(now), Arg::Int(id)])? == 1)
    }

    pub fn delete(&self, id: i64) -> Result<bool, String> {
        Ok(self.conn.run("DELETE FROM items WHERE id = ?", &[Arg::Int(id)])? == 1)
    }

    pub fn pin(&self, id: i64, pinned: bool) -> Result<bool, String> {
        Ok(self.conn.run("UPDATE items SET pinned = ? WHERE id = ?", &[Arg::Int(pinned as i64), Arg::Int(id)])? == 1)
    }

    pub fn clear(&self, keep_pinned: bool) -> Result<usize, String> {
        let n = if keep_pinned {
            self.conn.run("DELETE FROM items WHERE pinned = 0", &[])?
        } else {
            self.conn.run("DELETE FROM items", &[])?
        };
        // 지운 내용이 파일에 남지 않게 빈 공간을 정리한다(드물게만 실행).
        let _ = self.conn.exec("PRAGMA wal_checkpoint(TRUNCATE); VACUUM;");
        Ok(n)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn store() -> Store {
        Store::open(":memory:").unwrap()
    }

    impl Store {
        fn insert_plain(&self, kind: &str, data: &[u8], preview: &str, source: &str, now: f64)
                        -> Result<(i64, bool), String> {
            self.insert(kind, data, &[], preview, source, now)
        }
    }

    #[test]
    fn extra_formats_and_migration() {
        let s = store();
        let (id, _) = s.insert("text", b"hello", b"html-bytes", "hello", "", 1.0).unwrap();
        assert_eq!(s.payload(id).unwrap().unwrap().2, b"html-bytes".to_vec());
        let (again, new) = s.insert("text", b"hello", b"newer", "hello", "", 2.0).unwrap();
        assert!(!new && again == id);
        assert_eq!(s.payload(id).unwrap().unwrap().2, b"newer".to_vec());
        // v1 DB를 열면 extra 칸이 생긴다.
        let dir = std::env::temp_dir().join(format!("kagent-mig-{}", std::process::id()));
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("v1.db");
        let _ = std::fs::remove_file(&path);
        {
            let c = Connection::open(path.to_str().unwrap()).unwrap();
            c.exec("CREATE TABLE items(id INTEGER PRIMARY KEY, created REAL NOT NULL, used REAL NOT NULL,                     kind TEXT NOT NULL, hash TEXT NOT NULL UNIQUE, size INTEGER NOT NULL, pinned INTEGER NOT NULL                     DEFAULT 0, source TEXT NOT NULL DEFAULT '', preview BLOB NOT NULL, payload BLOB NOT NULL);                     PRAGMA user_version=1;").unwrap();
        }
        let migrated = Store::open(path.to_str().unwrap()).unwrap();
        let (mid, _) = migrated.insert("text", b"x", b"y", "x", "", 1.0).unwrap();
        assert_eq!(migrated.payload(mid).unwrap().unwrap().2, b"y".to_vec());
        drop(migrated);
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn schema_v2_migration_preserves_legacy_rows_and_extra() {
        let dir = std::env::temp_dir().join(format!("kagent-mig-v2-{}", std::process::id()));
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("v2.db");
        let _ = std::fs::remove_file(&path);
        {
            let c = Connection::open(path.to_str().unwrap()).unwrap();
            c.exec("CREATE TABLE items(id INTEGER PRIMARY KEY, created REAL NOT NULL, used REAL NOT NULL, kind TEXT NOT NULL, hash TEXT NOT NULL UNIQUE, size INTEGER NOT NULL, pinned INTEGER NOT NULL DEFAULT 0, source TEXT NOT NULL DEFAULT '', preview BLOB NOT NULL, payload BLOB NOT NULL, extra BLOB NOT NULL DEFAULT x''); PRAGMA user_version=2;").unwrap();
        }
        let migrated = Store::open(path.to_str().unwrap()).unwrap();
        let mut version = 0;
        migrated.conn.query("PRAGMA user_version", &[], |r| version = r.int(0)).unwrap();
        assert_eq!(version, 3);
        drop(migrated);
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn insert_dedupe_and_order() {
        let mut s = store();
        let (a, new_a) = s.insert_plain("text", "첫째".as_bytes(), "첫째", "notepad.exe", 1.0).unwrap();
        let (b, _) = s.insert_plain("text", "둘째".as_bytes(), "둘째", "", 2.0).unwrap();
        let (a2, new_a2) = s.insert_plain("text", "첫째".as_bytes(), "첫째", "", 3.0).unwrap();
        assert!(new_a && !new_a2);
        assert_eq!(a, a2);
        let ids: Vec<i64> = s.recent(10, None).unwrap().iter().map(|x| x.id).collect();
        assert_eq!(ids, vec![a, b]);
        assert_eq!(s.count().unwrap(), 2);
        assert_eq!(s.payload(a).unwrap().unwrap(), ("text".into(), "첫째".as_bytes().to_vec(), Vec::new()));
        assert_eq!(s.recent(10, Some("둘")).unwrap()[0].id, b);
    }

    #[test]
    fn list_filters_by_category_and_keyword_newest_first() {
        let mut s = store();
        let doc = s.insert_plain("text", "분기 보고서".as_bytes(), "분기 보고서", "hwp.exe", 1.0).unwrap().0;
        let url = s.insert_plain("text", b"https://example.com/a", "https://example.com/a", "notepad.exe", 2.0).unwrap().0;
        let shot = s.insert_plain("image", b"png", "캡처 · 그림 1x1", "screenshot", 3.0).unwrap().0;
        let file = s.insert_plain("files", "C:\\없는폴더\\넷째.hwpx\nC:\\없는폴더\\사진.png".as_bytes(), "파일 2개", "explorer.exe", 4.0).unwrap().0;
        let ids = |v: Vec<Summary>| v.iter().map(|x| x.id).collect::<Vec<_>>();
        assert_eq!(ids(s.list(50, Category::All, "").unwrap()), vec![file, shot, url, doc]);
        assert_eq!(ids(s.list(50, Category::Document, "").unwrap()), vec![file, doc]);
        assert_eq!(ids(s.list(50, Category::Image, "").unwrap()), vec![file, shot]);
        assert_eq!(ids(s.list(50, Category::Capture, "").unwrap()), vec![shot]);
        assert_eq!(ids(s.list(50, Category::Web, "").unwrap()), vec![url]);
        assert_eq!(ids(s.list(50, Category::File, "").unwrap()), vec![file]);
        assert!(s.list(50, Category::Folder, "").unwrap().is_empty());
        // 키워드: 파일 전체 경로까지, 한글 조합 중 글자도
        assert_eq!(ids(s.list(50, Category::All, "넷ㅉ").unwrap()), vec![file]);
        assert_eq!(ids(s.list(50, Category::All, "보고 분기").unwrap()), vec![doc]);
        assert_eq!(ids(s.list(1, Category::All, "").unwrap()), vec![file]);
        // recent()도 분류를 채운다(빠른 목록이 메모리에서 거를 수 있게)
        let recent = s.recent(10, None).unwrap();
        assert!(recent.iter().find(|x| x.id == shot).unwrap().cats.contains(Category::Capture));
        // 지운 항목은 캐시에서도 빠진다
        s.delete(doc).unwrap();
        assert_eq!(ids(s.list(50, Category::Document, "").unwrap()), vec![file]);
    }

    #[test]
    fn limits_keep_pinned() {
        let mut s = store();
        let mut settings = Settings::default();
        settings.max_items = 3;
        let pinned = s.insert_plain("text", b"pinned", "p", "", 0.5).unwrap().0;
        s.pin(pinned, true).unwrap();
        for i in 0..6 {
            s.insert_plain("text", format!("t{i}").as_bytes(), "x", "", 10.0 + i as f64).unwrap();
        }
        assert_eq!(s.enforce(&settings, 20.0).unwrap(), 3);
        assert_eq!(s.count().unwrap(), 4); // 고정 1 + 최근 3
        settings.max_age_days = 1.0;
        assert_eq!(s.enforce(&settings, 10.0 + 86400.0 * 2.0).unwrap(), 3);
        assert_eq!(s.recent(10, None).unwrap()[0].id, pinned);
        settings.max_total_bytes = 0;
        s.insert_plain("text", &[1u8; 100], "big", "", 1e9).unwrap();
        s.enforce(&settings, 1e9).unwrap();
        assert_eq!(s.count().unwrap(), 1); // 고정만 남음
        assert_eq!(s.clear(true).unwrap(), 0);
        assert_eq!(s.clear(false).unwrap(), 1);
    }

    #[test]
    fn settings_ranges() {
        let mut st = Settings::default();
        st.apply(&json::parse(r#"{"max_items":5,"max_total_mb":100,"auto_paste":false,"excluded_apps":["A.EXE"]}"#)
            .unwrap());
        assert_eq!(st.max_items, 50); // 10 미만은 무시
        assert_eq!(st.max_total_bytes, 100 * 1024 * 1024);
        assert!(!st.auto_paste);
        assert_eq!(st.excluded_apps, vec!["a.exe"]);
        let back = Settings::default();
        let mut again = Settings::default();
        again.apply(&back.to_json());
        assert_eq!(again.max_items, back.max_items);
    }

    #[test]
    fn popup_geometry_round_trips_and_rejects_unreasonable_values() {
        let mut settings = Settings::default();
        settings.apply(&json::parse(r#"{"popup_x":120,"popup_y":80,"popup_width":520,"popup_height":460}"#).unwrap());
        assert_eq!((settings.popup_x, settings.popup_y, settings.popup_width, settings.popup_height), (120, 80, 520, 460));
        let mut loaded = Settings::default();
        loaded.apply(&settings.to_json());
        assert_eq!((loaded.popup_x, loaded.popup_y, loaded.popup_width, loaded.popup_height), (120, 80, 520, 460));
        loaded.apply(&json::parse(r#"{"popup_x":900000,"popup_width":10,"popup_height":99999}"#).unwrap());
        assert_eq!((loaded.popup_x, loaded.popup_width, loaded.popup_height), (120, 520, 460));
    }

    #[test]
    fn screenshot_watch_defaults_on_and_existing_value_is_preserved() {
        let mut settings = Settings::default();
        assert!(settings.watch_screenshots);
        settings.apply(&json::parse(r#"{"watch_screenshots":false}"#).unwrap());
        assert!(!settings.watch_screenshots);
        let mut roundtrip = Settings::default();
        roundtrip.apply(&settings.to_json());
        assert!(!roundtrip.watch_screenshots);
    }

    #[test]
    fn collapsed_popup_setting_round_trips() {
        let mut settings = Settings::default();
        assert!(!settings.popup_collapsed);
        settings.apply(&json::parse(r#"{"popup_collapsed":true}"#).unwrap());
        assert!(settings.popup_collapsed);
        let mut loaded = Settings::default();
        loaded.apply(&settings.to_json());
        assert!(loaded.popup_collapsed);
    }
}
