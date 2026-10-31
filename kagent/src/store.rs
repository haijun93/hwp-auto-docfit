//! K클립보드 저장소(clip.db)와 설정(settings.json).
//!
//! - 내용(payload)과 미리보기는 DPAPI로 암호화해 저장한다.
//! - 같은 내용을 다시 복사하면 새로 쓰지 않고 순서만 앞으로 올린다(중복 0바이트).
//! - 한도: 고정하지 않은 항목 개수·전체 용량·보관 기간. 항목 하나의 상한은 기록 전에 막는다.

use crate::crypt;
use crate::json::{self, Value};
use crate::sqlite::{Arg, Connection};

/// 스키마 버전(PRAGMA user_version). 앱(kagent_client.py)이 같은 값을 확인한다.
#[allow(dead_code)]
pub const SCHEMA_VERSION: i64 = 1;

#[derive(Clone, Debug)]
pub struct Settings {
    pub max_items: i64,
    pub max_item_bytes: i64,
    pub max_total_bytes: i64,
    pub max_age_days: f64,
    pub auto_paste: bool,
    pub paused: bool,
    pub hotkey: String,
    pub excluded_apps: Vec<String>,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            max_items: 50,
            max_item_bytes: 10 * 1024 * 1024,
            max_total_bytes: 200 * 1024 * 1024,
            max_age_days: 30.0,
            auto_paste: true,
            paused: false,
            hotkey: "Ctrl+Shift+V".into(),
            // 암호 관리자는 제외 신호를 보내지만, 보내지 않는 프로그램도 있어 기본으로 뺀다.
            excluded_apps: ["keepass.exe", "keepassxc.exe", "1password.exe", "bitwarden.exe", "lastpass.exe"]
                .iter()
                .map(|s| s.to_string())
                .collect(),
        }
    }
}

impl Settings {
    pub fn to_json(&self) -> Value {
        Value::obj(vec![
            ("max_items", self.max_items.into()),
            ("max_item_mb", (self.max_item_bytes / 1024 / 1024).into()),
            ("max_total_mb", (self.max_total_bytes / 1024 / 1024).into()),
            ("max_age_days", self.max_age_days.into()),
            ("auto_paste", self.auto_paste.into()),
            ("paused", self.paused.into()),
            ("hotkey", self.hotkey.as_str().into()),
            ("excluded_apps", Value::Arr(self.excluded_apps.iter().map(|s| s.as_str().into()).collect())),
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
        if let Some(b) = v.bool("paused") {
            self.paused = b;
        }
        if let Some(s) = v.str("hotkey").filter(|s| s.len() <= 40) {
            self.hotkey = s.to_string();
        }
        if let Some(Value::Arr(items)) = v.get("excluded_apps") {
            self.excluded_apps = items
                .iter()
                .filter_map(|i| if let Value::Str(s) = i { Some(s.to_lowercase()) } else { None })
                .filter(|s| !s.is_empty() && s.len() <= 100)
                .take(100)
                .collect();
        }
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
    previews: std::collections::HashMap<i64, String>,
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
                source TEXT NOT NULL DEFAULT '', preview BLOB NOT NULL, payload BLOB NOT NULL);
             CREATE INDEX IF NOT EXISTS items_used ON items(used);
             PRAGMA user_version=1;",
        )?;
        Ok(Store { conn, previews: std::collections::HashMap::new() })
    }

    /// 새 항목이면 (id, true), 이미 있던 내용이면 (id, false)(순서만 앞으로).
    pub fn insert(&self, kind: &str, data: &[u8], preview: &str, source: &str, now: f64) -> Result<(i64, bool), String> {
        let hash = content_hash(kind, data);
        let mut existing = None;
        self.conn.query("SELECT id FROM items WHERE hash = ?", &[Arg::Text(&hash)], |r| existing = Some(r.int(0)))?;
        if let Some(id) = existing {
            self.conn.run("UPDATE items SET used = ? WHERE id = ?", &[Arg::Real(now), Arg::Int(id)])?;
            return Ok((id, false));
        }
        let sealed = crypt::protect(data).ok_or("암호화 실패")?;
        let sealed_preview = crypt::protect(preview.as_bytes()).ok_or("암호화 실패")?;
        self.conn.run(
            "INSERT INTO items(created, used, kind, hash, size, source, preview, payload) VALUES(?,?,?,?,?,?,?,?)",
            &[Arg::Real(now), Arg::Real(now), Arg::Text(kind), Arg::Text(&hash), Arg::Int(data.len() as i64),
              Arg::Text(source), Arg::Blob(&sealed_preview), Arg::Blob(&sealed)],
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
        let mut out = Vec::new();
        let cache = &mut self.previews;
        let mut seen = std::collections::HashSet::new();
        self.conn.query("SELECT id, kind, preview, pinned, used, size FROM items ORDER BY used DESC", &[], |r| {
            let id = r.int(0);
            seen.insert(id);
            if out.len() >= limit {
                return;
            }
            let preview = cache
                .entry(id)
                .or_insert_with(|| crypt::unprotect(&r.blob(2)).map(|b| String::from_utf8_lossy(&b).into_owned())
                    .unwrap_or_default())
                .clone();
            if let Some(n) = &needle {
                if !preview.to_lowercase().contains(n.as_str()) {
                    return;
                }
            }
            out.push(Summary { id, kind: r.text(1), preview, pinned: r.int(3) != 0, used: r.real(4), size: r.int(5) });
        })?;
        cache.retain(|id, _| seen.contains(id));
        Ok(out)
    }

    pub fn payload(&self, id: i64) -> Result<Option<(String, Vec<u8>)>, String> {
        let mut found = None;
        self.conn.query("SELECT kind, payload FROM items WHERE id = ?", &[Arg::Int(id)], |r| {
            found = Some((r.text(0), r.blob(1)))
        })?;
        Ok(match found {
            Some((kind, sealed)) => Some((kind, crypt::unprotect(&sealed).ok_or("복호화 실패")?)),
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

    #[test]
    fn insert_dedupe_and_order() {
        let mut s = store();
        let (a, new_a) = s.insert("text", "첫째".as_bytes(), "첫째", "notepad.exe", 1.0).unwrap();
        let (b, _) = s.insert("text", "둘째".as_bytes(), "둘째", "", 2.0).unwrap();
        let (a2, new_a2) = s.insert("text", "첫째".as_bytes(), "첫째", "", 3.0).unwrap();
        assert!(new_a && !new_a2);
        assert_eq!(a, a2);
        let ids: Vec<i64> = s.recent(10, None).unwrap().iter().map(|x| x.id).collect();
        assert_eq!(ids, vec![a, b]);
        assert_eq!(s.count().unwrap(), 2);
        assert_eq!(s.payload(a).unwrap().unwrap(), ("text".into(), "첫째".as_bytes().to_vec()));
        assert_eq!(s.recent(10, Some("둘")).unwrap()[0].id, b);
    }

    #[test]
    fn limits_keep_pinned() {
        let mut s = store();
        let mut settings = Settings::default();
        settings.max_items = 3;
        let pinned = s.insert("text", b"pinned", "p", "", 0.5).unwrap().0;
        s.pin(pinned, true).unwrap();
        for i in 0..6 {
            s.insert("text", format!("t{i}").as_bytes(), "x", "", 10.0 + i as f64).unwrap();
        }
        assert_eq!(s.enforce(&settings, 20.0).unwrap(), 3);
        assert_eq!(s.count().unwrap(), 4); // 고정 1 + 최근 3
        settings.max_age_days = 1.0;
        assert_eq!(s.enforce(&settings, 10.0 + 86400.0 * 2.0).unwrap(), 3);
        assert_eq!(s.recent(10, None).unwrap()[0].id, pinned);
        settings.max_total_bytes = 0;
        s.insert("text", &[1u8; 100], "big", "", 1e9).unwrap();
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
}
