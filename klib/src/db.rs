//! SQLite(rusqlite bundled) 기반 가상 관계형 자료함 DB 모듈.

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use rusqlite::{params, Connection, OptionalExtension, Result};

use crate::util::{data_dir, is_or_has_reparse_point, now, now_ms, sanitize_filename};

static ITEM_FILE_SEQ: AtomicU64 = AtomicU64::new(1);

pub struct BoxRow {
    pub id: i64,
    pub name: String,
    pub description: String,
    pub created_at: f64,
    pub updated_at: f64,
    pub export_path: Option<String>,
    pub item_count: i64,
}

pub struct ItemRow {
    pub id: i64,
    pub box_id: i64,
    pub kind: String,
    pub source_path: String,
    pub display_name: String,
    pub space: String,
    pub x: f64,
    pub y: f64,
    pub created_at: f64,
}

pub struct RelationRow {
    pub id: i64,
    pub box_id: i64,
    pub from_item: i64,
    pub to_item: i64,
    pub label: String,
}

pub struct Database {
    conn: Connection,
}

impl Database {
    pub(crate) fn connection(&self) -> &Connection { &self.conn }

    pub fn notebook_create(&self,name:&str,description:&str)->Result<i64>{crate::notebook::create(&self.conn,name,description)}
    pub fn notebook_update(&self,id:i64,name:&str,description:&str)->Result<bool>{crate::notebook::update(&self.conn,id,name,description)}
    pub fn notebook_delete(&self,id:i64)->Result<bool>{crate::notebook::delete(&self.conn,id)}
    pub fn notebook_sources(&self,id:i64)->Result<Vec<crate::notebook::Source>>{crate::notebook::sources(&self.conn,id)}
    pub fn notebook_source_paragraphs(&self,notebook_id:i64,source_id:i64)->Result<Vec<crate::notebook::Paragraph>>{crate::notebook::source_paragraphs(&self.conn,notebook_id,source_id)}
    pub fn notebook_notes(&self,notebook_id:i64)->Result<Vec<(i64,String,String,i64)>>{let mut s=self.conn.prepare("SELECT id,title,body,updated_at FROM nb_note WHERE notebook_id=?1 ORDER BY updated_at DESC,id DESC")?;s.query_map([notebook_id],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?)))?.collect()}
}

impl Database {
    pub fn open(db_path: &str) -> Result<Self> {
        if let Some(parent) = Path::new(db_path).parent() {
            let _ = fs::create_dir_all(parent);
        }
        let conn = Connection::open(db_path)?;
        let db = Database { conn };
        db.init_schema()?;
        crate::notebook::init_schema(&db.conn)?;
        crate::scan::init_schema(&db.conn)?;
        Ok(db)
    }

    pub fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            "PRAGMA foreign_keys = ON;
             PRAGMA journal_mode = WAL;

             CREATE TABLE IF NOT EXISTS box (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 description TEXT NOT NULL DEFAULT '',
                 created_at REAL NOT NULL,
                 updated_at REAL NOT NULL,
                 export_path TEXT
             );

             CREATE TABLE IF NOT EXISTS item (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 box_id INTEGER NOT NULL REFERENCES box(id) ON DELETE CASCADE,
                 kind TEXT NOT NULL,
                 source_path TEXT NOT NULL DEFAULT '',
                 display_name TEXT NOT NULL,
                 space TEXT NOT NULL DEFAULT 'temp',
                 x REAL NOT NULL DEFAULT 0.0,
                 y REAL NOT NULL DEFAULT 0.0,
                 created_at REAL NOT NULL,
                 UNIQUE (box_id, id)
             );

             CREATE TABLE IF NOT EXISTS relation (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 box_id INTEGER NOT NULL REFERENCES box(id) ON DELETE CASCADE,
                 from_item INTEGER NOT NULL,
                 to_item INTEGER NOT NULL,
                 label TEXT NOT NULL DEFAULT '',
                 FOREIGN KEY (box_id, from_item) REFERENCES item(box_id, id) ON DELETE CASCADE,
                 FOREIGN KEY (box_id, to_item) REFERENCES item(box_id, id) ON DELETE CASCADE
             );

             CREATE INDEX IF NOT EXISTS idx_item_box_space ON item(box_id, space);
             CREATE INDEX IF NOT EXISTS idx_item_display_name ON item(display_name);
             CREATE INDEX IF NOT EXISTS idx_relation_box ON relation(box_id);
             CREATE INDEX IF NOT EXISTS idx_relation_endpoints ON relation(from_item, to_item);",
        )?;
        Ok(())
    }

    // --- Box CRUD ---

    pub fn box_create(&self, name: &str, description: &str) -> Result<i64> {
        let t = now();
        self.conn.execute(
            "INSERT INTO box (name, description, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
            params![name, description, t, t],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn box_list(&self) -> Result<Vec<BoxRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT b.id, b.name, b.description, b.created_at, b.updated_at, b.export_path,
                    (SELECT COUNT(*) FROM item WHERE box_id = b.id) AS item_count
             FROM box b ORDER BY b.updated_at DESC",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(BoxRow {
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                created_at: row.get(3)?,
                updated_at: row.get(4)?,
                export_path: row.get(5)?,
                item_count: row.get(6)?,
            })
        })?;
        let mut list = Vec::new();
        for r in rows {
            list.push(r?);
        }
        Ok(list)
    }

    pub fn box_get(&self, id: i64) -> Result<Option<(BoxRow, Vec<ItemRow>, Vec<RelationRow>)>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, description, created_at, updated_at, export_path,
                    (SELECT COUNT(*) FROM item WHERE box_id = ?1)
             FROM box WHERE id = ?1",
        )?;
        let mut rows = stmt.query(params![id])?;
        let Some(row) = rows.next()? else {
            return Ok(None);
        };
        let b = BoxRow {
            id: row.get(0)?,
            name: row.get(1)?,
            description: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
            export_path: row.get(5)?,
            item_count: row.get(6)?,
        };

        // Items
        let mut item_stmt = self.conn.prepare(
            "SELECT id, box_id, kind, source_path, display_name, space, x, y, created_at
             FROM item WHERE box_id = ?1 ORDER BY id ASC",
        )?;
        let item_rows = item_stmt.query_map(params![id], |r| {
            Ok(ItemRow {
                id: r.get(0)?,
                box_id: r.get(1)?,
                kind: r.get(2)?,
                source_path: r.get(3)?,
                display_name: r.get(4)?,
                space: r.get(5)?,
                x: r.get(6)?,
                y: r.get(7)?,
                created_at: r.get(8)?,
            })
        })?;
        let mut items = Vec::new();
        for it in item_rows {
            items.push(it?);
        }

        // Relations
        let mut rel_stmt = self.conn.prepare(
            "SELECT id, box_id, from_item, to_item, label
             FROM relation WHERE box_id = ?1 ORDER BY id ASC",
        )?;
        let rel_rows = rel_stmt.query_map(params![id], |r| {
            Ok(RelationRow {
                id: r.get(0)?,
                box_id: r.get(1)?,
                from_item: r.get(2)?,
                to_item: r.get(3)?,
                label: r.get(4)?,
            })
        })?;
        let mut relations = Vec::new();
        for rl in rel_rows {
            relations.push(rl?);
        }

        Ok(Some((b, items, relations)))
    }

    pub fn box_rename(&self, id: i64, name: &str) -> Result<bool> {
        let affected = self.conn.execute("UPDATE box SET name = ?1, updated_at = ?2 WHERE id = ?3", params![name, now(), id])?;
        Ok(affected > 0)
    }

    pub fn box_update(&self, id: i64, name: &str, description: &str) -> Result<bool> {
        let t = now();
        let affected = self.conn.execute(
            "UPDATE box SET name = ?1, description = ?2, updated_at = ?3 WHERE id = ?4",
            params![name, description, t, id],
        )?;
        Ok(affected > 0)
    }

    pub fn box_delete(&self, id: i64) -> Result<bool> {
        let affected = self.conn.execute("DELETE FROM box WHERE id = ?1", params![id])?;
        if affected > 0 {
            // 사본 데이터 폴더 정리
            let box_dir = PathBuf::from(data_dir()).join("boxes").join(id.to_string());
            let _ = fs::remove_dir_all(box_dir);
        }
        Ok(affected > 0)
    }

    // --- Item CRUD & Operations ---

    pub fn item_add(
        &self,
        box_id: i64,
        kind: &str,
        source_path: &str,
        display_name: &str,
        space: &str,
        x: f64,
        y: f64,
        content: Option<&str>,
    ) -> std::result::Result<i64, String> {
        // 1. 종류 및 공간 유효성 검증
        match kind {
            "file" | "folder" | "link" | "text" | "rich_text" | "image" | "capture" | "note" => {}
            _ => return Err(format!("지원하지 않는 자료 종류입니다: {kind}")),
        }
        match space {
            "core" | "basis" | "reference" | "temp" => {}
            _ => return Err(format!("유효하지 않은 공간입니다: {space}")),
        }

        // 2. 대상 box 존재 여부 DB 확인
        let box_exists: bool = self.conn.query_row(
            "SELECT EXISTS(SELECT 1 FROM box WHERE id = ?1)",
            params![box_id],
            |r| r.get(0),
        ).map_err(|e| e.to_string())?;
        if !box_exists {
            return Err(format!("자료함(box_id={box_id})이 존재하지 않습니다."));
        }

        // 3. 심볼릭 링크/정션(상위 경로 포함) 및 파일/폴더 종류·존재 여부 검증 (지적 1 반영)
        if !source_path.is_empty() {
            let p = Path::new(source_path);
            if is_or_has_reparse_point(p) {
                return Err("심볼릭 링크나 정션(또는 그 하위 경로)은 추가할 수 없습니다.".into());
            }
            if kind == "file" && !p.is_file() {
                return Err(format!("원본 파일을 찾을 수 없습니다: {source_path}"));
            }
            if kind == "folder" && !p.is_dir() {
                return Err(format!("원본 폴더를 찾을 수 없습니다: {source_path}"));
            }
        } else if matches!(kind, "file" | "folder") {
            return Err("파일 또는 폴더 경로는 비어있을 수 없습니다.".into());
        }

        let mut actual_source = source_path.to_string();
        let mut created_file_to_cleanup: Option<PathBuf> = None;

        // 4. 글·그림 사본 생성 및 고유 파일명 보장 (지적 6 반영)
        let base_dir = PathBuf::from(data_dir()).join("boxes").join(box_id.to_string()).join("items");
        if matches!(kind, "text" | "rich_text" | "note") {
            fs::create_dir_all(&base_dir).map_err(|e| format!("데이터 디렉터리 생성 실패: {e}"))?;
            let ext = if kind == "rich_text" { "json" } else { "txt" };
            let clean_title = sanitize_filename(display_name);
            let seq = ITEM_FILE_SEQ.fetch_add(1, Ordering::Relaxed);
            let base_filename = format!("{}_{}_{}.{}", now_ms(), seq, clean_title, ext);
            let target_file = unique_path(&base_dir, &base_filename);
            let text_to_save = content.unwrap_or(source_path);
            fs::write(&target_file, text_to_save).map_err(|e| format!("글 사본 생성 실패: {e}"))?;
            actual_source = target_file.to_string_lossy().to_string();
            created_file_to_cleanup = Some(target_file);
        } else if matches!(kind, "image" | "capture") {
            fs::create_dir_all(&base_dir).map_err(|e| format!("데이터 디렉터리 생성 실패: {e}"))?;
            let clean_title = sanitize_filename(display_name);
            let seq = ITEM_FILE_SEQ.fetch_add(1, Ordering::Relaxed);
            let base_filename = format!("{}_{}_{}.png", now_ms(), seq, clean_title);
            let target_file = unique_path(&base_dir, &base_filename);
            if let Some(b64) = content {
                let bytes = crate::util::base64_decode(b64)
                    .ok_or_else(|| "Base64 디코딩 실패".to_string())?;
                fs::write(&target_file, bytes).map_err(|e| format!("그림 사본 저장 실패: {e}"))?;
                actual_source = target_file.to_string_lossy().to_string();
                created_file_to_cleanup = Some(target_file);
            } else if !source_path.is_empty() {
                let src_p = Path::new(source_path);
                if is_or_has_reparse_point(src_p) {
                    return Err("심볼릭 링크나 정션은 추가할 수 없습니다.".into());
                }
                if !src_p.is_file() {
                    return Err(format!("원본 이미지 파일을 찾을 수 없습니다: {source_path}"));
                }
                fs::copy(src_p, &target_file).map_err(|e| format!("그림 사본 복사 실패: {e}"))?;
                actual_source = target_file.to_string_lossy().to_string();
                created_file_to_cleanup = Some(target_file);
            }
        }

        // 5. DB 행 삽입 및 실패 시 생성된 사본 파일 롤백/정리
        let t = now();
        let insert_res = self.conn.execute(
            "INSERT INTO item (box_id, kind, source_path, display_name, space, x, y, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![box_id, kind, actual_source, display_name, space, x, y, t],
        );

        match insert_res {
            Ok(_) => {
                let item_id = self.conn.last_insert_rowid();
                let _ = self.conn.execute("UPDATE box SET updated_at = ?1 WHERE id = ?2", params![t, box_id]);
                Ok(item_id)
            }
            Err(e) => {
                if let Some(created_path) = created_file_to_cleanup {
                    let _ = fs::remove_file(created_path);
                }
                Err(format!("아이템 DB 등록 실패: {e}"))
            }
        }
    }

    pub fn item_get(&self, id: i64) -> Result<Option<ItemRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, box_id, kind, source_path, display_name, space, x, y, created_at
             FROM item WHERE id = ?1",
        )?;
        let mut rows = stmt.query(params![id])?;
        if let Some(r) = rows.next()? {
            Ok(Some(ItemRow {
                id: r.get(0)?,
                box_id: r.get(1)?,
                kind: r.get(2)?,
                source_path: r.get(3)?,
                display_name: r.get(4)?,
                space: r.get(5)?,
                x: r.get(6)?,
                y: r.get(7)?,
                created_at: r.get(8)?,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn item_update(&self, id: i64, display_name: &str) -> Result<bool> {
        let affected = self.conn.execute(
            "UPDATE item SET display_name = ?1 WHERE id = ?2",
            params![display_name, id],
        )?;
        Ok(affected > 0)
    }

    /// 글 자료(text·note)의 klib 사본 파일. 자료함 데이터 폴더(boxes/<box_id>/items) 바로 아래 .txt만 허용한다.
    /// 화면의 메모 편집기가 고치는 대상이 사용자 원본이나 임의 경로가 되지 않게 막는다.
    fn item_text_copy(&self, id: i64) -> std::result::Result<(ItemRow, PathBuf), String> {
        let it = self.item_get(id).map_err(|e| e.to_string())?
            .ok_or_else(|| "해당 자료 항목을 찾을 수 없습니다.".to_string())?;
        if !matches!(it.kind.as_str(), "text" | "note") {
            return Err("글 자료(text·note)만 메모 편집기로 열 수 있습니다.".into());
        }
        let path = PathBuf::from(&it.source_path);
        let is_txt = path.extension().and_then(|e| e.to_str()).is_some_and(|e| e.eq_ignore_ascii_case("txt"));
        if !is_txt || is_or_has_reparse_point(&path) || !path.is_file() {
            return Err("글 자료의 사본 파일을 찾을 수 없습니다.".into());
        }
        let base = PathBuf::from(data_dir()).join("boxes").join(it.box_id.to_string()).join("items");
        let inside = match (base.canonicalize(), path.parent().map(Path::canonicalize)) {
            (Ok(b), Some(Ok(p))) => b == p,
            _ => false,
        };
        if !inside {
            return Err("자료함 데이터 폴더 밖의 파일은 편집할 수 없습니다.".into());
        }
        Ok((it, path))
    }

    /// 글 자료 내용 읽기(메모 편집기로 열기).
    pub fn item_text_get(&self, id: i64) -> std::result::Result<(ItemRow, String), String> {
        let (it, path) = self.item_text_copy(id)?;
        let bytes = fs::read(&path).map_err(|e| format!("글 사본 읽기 실패: {e}"))?;
        Ok((it, String::from_utf8_lossy(&bytes).into_owned()))
    }

    /// 글 자료 내용(과 이름) 고치기. 임시 파일에 쓴 뒤 바꿔치기해 중간에 실패해도 사본이 반쯤 쓰이지 않게 한다.
    /// 돌려주는 값은 다시 색인할 때 쓰는 고친 뒤의 항목.
    pub fn item_text_set(&self, id: i64, content: &str, display_name: Option<&str>) -> std::result::Result<ItemRow, String> {
        let (mut it, path) = self.item_text_copy(id)?;
        let tmp = path.with_extension(format!("txt.{}.tmp", now_ms()));
        fs::write(&tmp, content).map_err(|e| format!("글 사본 쓰기 실패: {e}"))?;
        if let Err(e) = fs::rename(&tmp, &path) {
            let _ = fs::remove_file(&tmp);
            return Err(format!("글 사본 바꾸기 실패: {e}"));
        }
        let t = now();
        if let Some(name) = display_name.map(str::trim).filter(|n| !n.is_empty()) {
            self.conn.execute("UPDATE item SET display_name = ?1 WHERE id = ?2", params![name, id])
                .map_err(|e| e.to_string())?;
            it.display_name = name.to_string();
        }
        let _ = self.conn.execute("UPDATE box SET updated_at = ?1 WHERE id = ?2", params![t, it.box_id]);
        Ok(it)
    }

    pub fn item_move(&self, id: i64, space: &str, x: f64, y: f64) -> std::result::Result<bool, String> {
        match space {
            "core" | "basis" | "reference" | "temp" => {}
            _ => return Err(format!("유효하지 않은 공간입니다: {space}")),
        }
        let affected = self.conn.execute(
            "UPDATE item SET space = ?1, x = ?2, y = ?3 WHERE id = ?4",
            params![space, x, y, id],
        ).map_err(|e| e.to_string())?;
        Ok(affected > 0)
    }

    pub fn item_delete(&self, id: i64) -> Result<bool> {
        let affected = self.conn.execute("DELETE FROM item WHERE id = ?1", params![id])?;
        Ok(affected > 0)
    }

    pub fn item_delete_source(&self, id: i64) -> Result<Option<String>> {
        let source = self.conn.query_row("SELECT source_path FROM item WHERE id=?1", params![id], |r| r.get::<_, String>(0)).optional()?;
        self.item_delete(id)?;
        Ok(source)
    }

    pub fn item_search(&self, box_id: Option<i64>, query: &str) -> Result<Vec<ItemRow>> {
        let pattern = format!("%{query}%");
        let (sql, params_vec): (&str, Vec<rusqlite::types::Value>) = match box_id {
            Some(bid) => (
                "SELECT id, box_id, kind, source_path, display_name, space, x, y, created_at
                 FROM item
                 WHERE box_id = ?1 AND (display_name LIKE ?2 COLLATE NOCASE OR source_path LIKE ?2 COLLATE NOCASE)
                 ORDER BY id DESC",
                vec![bid.into(), pattern.into()],
            ),
            None => (
                "SELECT id, box_id, kind, source_path, display_name, space, x, y, created_at
                 FROM item
                 WHERE display_name LIKE ?1 COLLATE NOCASE OR source_path LIKE ?1 COLLATE NOCASE
                 ORDER BY id DESC",
                vec![pattern.into()],
            ),
        };
        let mut stmt = self.conn.prepare(sql)?;
        let rows = stmt.query_map(rusqlite::params_from_iter(params_vec), |r| {
            Ok(ItemRow {
                id: r.get(0)?,
                box_id: r.get(1)?,
                kind: r.get(2)?,
                source_path: r.get(3)?,
                display_name: r.get(4)?,
                space: r.get(5)?,
                x: r.get(6)?,
                y: r.get(7)?,
                created_at: r.get(8)?,
            })
        })?;
        let mut items = Vec::new();
        for it in rows {
            items.push(it?);
        }
        Ok(items)
    }

    pub fn item_rename(&self, id: i64, name: &str) -> Result<bool> {
        Ok(self.conn.execute("UPDATE item SET display_name=?1 WHERE id=?2", params![name,id])? > 0)
    }

    pub fn relation_update(&self, id: i64, label: &str) -> Result<bool> {
        Ok(self.conn.execute("UPDATE relation SET label = ?1 WHERE id = ?2", params![label, id])? > 0)
    }

    // --- Relation CRUD ---

    pub fn relation_add(&self, box_id: i64, from_item: i64, to_item: i64, label: &str) -> std::result::Result<i64, String> {
        // 1. 자기 자신에 대한 관계선 금지
        if from_item == to_item {
            return Err("자기 자신에 대한 관계선은 허용되지 않습니다.".into());
        }

        // 2. 대상 box 존재 여부 DB 확인 (지적 2 반영)
        let box_exists: bool = self.conn.query_row(
            "SELECT EXISTS(SELECT 1 FROM box WHERE id = ?1)",
            params![box_id],
            |r| r.get(0),
        ).map_err(|e| e.to_string())?;
        if !box_exists {
            return Err(format!("자료함(box_id={box_id})이 존재하지 않습니다."));
        }

        // 3. 양 끝 항목이 모두 지정된 동일 box_id에 존재하는지 검증 (지적 2 반영)
        let from_box: Option<i64> = self.conn.query_row(
            "SELECT box_id FROM item WHERE id = ?1",
            params![from_item],
            |r| r.get(0),
        ).optional().map_err(|e| e.to_string())?;

        let to_box: Option<i64> = self.conn.query_row(
            "SELECT box_id FROM item WHERE id = ?1",
            params![to_item],
            |r| r.get(0),
        ).optional().map_err(|e| e.to_string())?;

        match (from_box, to_box) {
            (Some(b1), Some(b2)) if b1 == box_id && b2 == box_id => {}
            _ => return Err("지정된 항목이 해당 자료함에 존재하지 않습니다.".into()),
        }

        self.conn.execute(
            "INSERT INTO relation (box_id, from_item, to_item, label) VALUES (?1, ?2, ?3, ?4)",
            params![box_id, from_item, to_item, label],
        ).map_err(|e| e.to_string())?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn relation_delete(&self, id: i64) -> Result<bool> {
        let affected = self.conn.execute("DELETE FROM relation WHERE id = ?1", params![id])?;
        Ok(affected > 0)
    }

    pub fn relation_list(&self, box_id: i64) -> Result<Vec<RelationRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, box_id, from_item, to_item, label FROM relation WHERE box_id = ?1 ORDER BY id ASC",
        )?;
        let rows = stmt.query_map(params![box_id], |r| {
            Ok(RelationRow {
                id: r.get(0)?,
                box_id: r.get(1)?,
                from_item: r.get(2)?,
                to_item: r.get(3)?,
                label: r.get(4)?,
            })
        })?;
        let mut list = Vec::new();
        for r in rows {
            list.push(r?);
        }
        Ok(list)
    }

    // --- 물리 폴더 전환 (Export) ---

    pub fn box_export(&self, box_id: i64, target_dir: &str) -> std::result::Result<usize, String> {
        // 1. 자료함 존재 확인
        let box_exists: bool = self.conn.query_row(
            "SELECT EXISTS(SELECT 1 FROM box WHERE id = ?1)",
            params![box_id],
            |r| r.get(0),
        ).map_err(|e| e.to_string())?;
        if !box_exists {
            return Err(format!("자료함(box_id={box_id})이 존재하지 않습니다."));
        }

        // 2. 대상 폴더 검증 (지적 3 반영: 이미 존재하는 폴더인 경우 빈 폴더인지 검증)
        let target = Path::new(target_dir);
        let target_existed = target.exists();
        if target_existed {
            if !target.is_dir() {
                return Err(format!("내보내기 대상 경로가 디렉터리가 아닙니다: {target_dir}"));
            }
            let mut entries = fs::read_dir(target).map_err(|e| format!("대상 폴더 읽기 실패: {e}"))?;
            if entries.next().is_some() {
                return Err(format!("내보내기 대상 폴더가 비어있지 않습니다: {target_dir}"));
            }
        } else {
            fs::create_dir_all(target).map_err(|e| format!("대상 폴더 생성 실패: {e}"))?;
        }

        // 공간별 4개 하위 폴더 생성
        let core_dir = target.join("1_핵심자료");
        let basis_dir = target.join("2_기초자료");
        let ref_dir = target.join("3_참고자료");
        let temp_dir = target.join("4_임시저장소");

        let cleanup_export = || {
            if !target_existed {
                let _ = fs::remove_dir_all(target);
            } else {
                let _ = fs::remove_dir_all(&core_dir);
                let _ = fs::remove_dir_all(&basis_dir);
                let _ = fs::remove_dir_all(&ref_dir);
                let _ = fs::remove_dir_all(&temp_dir);
            }
        };

        for dir in [&core_dir, &basis_dir, &ref_dir, &temp_dir] {
            if let Err(e) = fs::create_dir_all(dir) {
                cleanup_export();
                return Err(format!("하위 폴더 생성 실패: {e}"));
            }
        }

        let mut item_stmt = self.conn.prepare(
            "SELECT id, kind, source_path, display_name, space FROM item WHERE box_id = ?1",
        ).map_err(|e| {
            cleanup_export();
            e.to_string()
        })?;

        let rows = item_stmt.query_map(params![box_id], |r| {
            Ok((
                r.get::<_, i64>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
                r.get::<_, String>(4)?,
            ))
        }).map_err(|e| {
            cleanup_export();
            e.to_string()
        })?;

        let mut exported_count = 0;

        for item_res in rows {
            let (_id, kind, source_path, display_name, space) = match item_res {
                Ok(data) => data,
                Err(e) => {
                    cleanup_export();
                    return Err(e.to_string());
                }
            };

            let dest_folder = match space.as_str() {
                "core" => &core_dir,
                "basis" => &basis_dir,
                "reference" => &ref_dir,
                _ => &temp_dir,
            };

            match kind.as_str() {
                "file" => {
                    let src = Path::new(&source_path);
                    if is_or_has_reparse_point(src) {
                        cleanup_export();
                        return Err(format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {source_path}"));
                    }
                    if !src.is_file() {
                        cleanup_export();
                        return Err(format!("원본 파일을 찾을 수 없습니다: {source_path}"));
                    }
                    let filename = if display_name.is_empty() {
                        src.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| "file.dat".into())
                    } else {
                        sanitize_filename(&display_name)
                    };
                    let dest_path = unique_path(dest_folder, &filename);
                    if dest_path.parent() != Some(dest_folder) {
                        cleanup_export();
                        return Err(format!("잘못된 대상 파일 경로입니다: {}", dest_path.display()));
                    }
                    if let Err(e) = fs::copy(src, &dest_path) {
                        cleanup_export();
                        return Err(format!("파일 복사 실패 ({source_path}): {e}"));
                    }
                    exported_count += 1;
                }
                "folder" => {
                    let src = Path::new(&source_path);
                    if is_or_has_reparse_point(src) {
                        cleanup_export();
                        return Err(format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {source_path}"));
                    }
                    if !src.is_dir() {
                        cleanup_export();
                        return Err(format!("원본 폴더를 찾을 수 없습니다: {source_path}"));
                    }
                    let folder_name = if display_name.is_empty() {
                        src.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| "folder".into())
                    } else {
                        sanitize_filename(&display_name)
                    };
                    let dest_path = unique_path(dest_folder, &folder_name);
                    if dest_path.parent() != Some(dest_folder) {
                        cleanup_export();
                        return Err(format!("잘못된 대상 폴더 경로입니다: {}", dest_path.display()));
                    }
                    if let Err(e) = copy_dir_recursive(src, &dest_path) {
                        cleanup_export();
                        return Err(format!("폴더 복사 실패 ({source_path}): {e}"));
                    }
                    exported_count += 1;
                }
                "text" | "rich_text" | "note" => {
                    let clean_name = sanitize_filename(&display_name);
                    let ext = if kind == "rich_text" { "html" } else { "txt" };
                    let filename = if clean_name.to_ascii_lowercase().ends_with(&format!(".{ext}")) {
                        clean_name
                    } else {
                        format!("{clean_name}.{ext}")
                    };
                    let dest_path = unique_path(dest_folder, &filename);
                    if dest_path.parent() != Some(dest_folder) {
                        cleanup_export();
                        return Err(format!("잘못된 대상 경로입니다: {}", dest_path.display()));
                    }
                    let src = Path::new(&source_path);
                    if kind == "rich_text" && src.is_file() {
                        if is_or_has_reparse_point(src) { cleanup_export(); return Err("reparse point".into()); }
                        if let Err(e) = fs::copy(src, &dest_path) { cleanup_export(); return Err(format!("HTML export failed: {e}")); }
                    } else if src.is_file() {
                        if is_or_has_reparse_point(src) {
                            cleanup_export();
                            return Err(format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {source_path}"));
                        }
                        if let Err(e) = fs::copy(src, &dest_path) {
                            cleanup_export();
                            return Err(format!("글 사본 복사 실패: {e}"));
                        }
                    } else if let Err(e) = fs::write(&dest_path, &source_path) {
                        cleanup_export();
                        return Err(format!("글 파일 저장 실패: {e}"));
                    }
                    exported_count += 1;
                }
                "image" | "capture" => {
                    let clean_name = sanitize_filename(&display_name);
                    let filename = if clean_name.ends_with(".png") || clean_name.ends_with(".jpg") || clean_name.ends_with(".jpeg") {
                        clean_name
                    } else {
                        format!("{clean_name}.png")
                    };
                    let dest_path = unique_path(dest_folder, &filename);
                    if dest_path.parent() != Some(dest_folder) {
                        cleanup_export();
                        return Err(format!("잘못된 대상 경로입니다: {}", dest_path.display()));
                    }
                    let src = Path::new(&source_path);
                    if is_or_has_reparse_point(src) {
                        cleanup_export();
                        return Err(format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {source_path}"));
                    }
                    if !src.is_file() {
                        cleanup_export();
                        return Err(format!("원본 이미지 파일을 찾을 수 없습니다: {source_path}"));
                    }
                    if let Err(e) = fs::copy(src, &dest_path) {
                        cleanup_export();
                        return Err(format!("이미지 복사 실패: {e}"));
                    }
                    exported_count += 1;
                }
                "link" => {
                    let clean_name = sanitize_filename(&display_name);
                    let filename = if clean_name.ends_with(".url") {
                        clean_name
                    } else {
                        format!("{clean_name}.url")
                    };
                    let dest_path = unique_path(dest_folder, &filename);
                    if dest_path.parent() != Some(dest_folder) {
                        cleanup_export();
                        return Err(format!("잘못된 대상 경로입니다: {}", dest_path.display()));
                    }
                    let shortcut_content = format!("[InternetShortcut]\r\nURL={source_path}\r\n");
                    if let Err(e) = fs::write(&dest_path, shortcut_content) {
                        cleanup_export();
                        return Err(format!("바로가기 링크 생성 실패: {e}"));
                    }
                    exported_count += 1;
                }
                _ => {}
            }
        }

        let t = now();
        if let Err(e) = self.conn.execute(
            "UPDATE box SET export_path = ?1, updated_at = ?2 WHERE id = ?3",
            params![target_dir, t, box_id],
        ) {
            cleanup_export();
            return Err(format!("자료함 전환 정보 갱신 실패: {e}"));
        }

        Ok(exported_count)
    }
}

/// 파일명 충돌 회피: 동일 파일명이 존재할 경우 "이름 (1).ext", "이름 (2).ext" 형태로 새 경로 반환.
fn unique_path(dir: &Path, filename: &str) -> PathBuf {
    let target = dir.join(filename);
    if !target.exists() {
        return target;
    }
    let p = Path::new(filename);
    let stem = p.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_else(|| filename.to_string());
    let ext = p.extension().map(|e| format!(".{}", e.to_string_lossy())).unwrap_or_default();

    let mut counter = 1;
    loop {
        let candidate = dir.join(format!("{stem} ({counter}){ext}"));
        if !candidate.exists() {
            return candidate;
        }
        counter += 1;
    }
}

/// 디렉터리 재귀 복사 (링크·정션 발견 시 명시적 오류 반환, 내부 파일명 충돌 회피, 복사 실패 에러 전파)
pub(crate) fn copy_dir_recursive(src: &Path, dst: &Path) -> std::io::Result<()> {
    if is_or_has_reparse_point(src) {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {}", src.display()),
        ));
    }
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let path = entry.path();
        if is_or_has_reparse_point(&path) {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!("심볼릭 링크나 정션은 내보낼 수 없습니다: {}", path.display()),
            ));
        }
        let file_name = entry.file_name();
        let name_str = file_name.to_string_lossy();
        let safe_name = sanitize_filename(&name_str);
        if path.is_dir() {
            let dest_child = unique_path(dst, &safe_name);
            copy_dir_recursive(&path, &dest_child)?;
        } else {
            let dest_child = unique_path(dst, &safe_name);
            fs::copy(&path, &dest_child)?;
        }
    }
    Ok(())
}
