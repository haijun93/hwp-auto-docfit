"""Small SQLite metadata store, intentionally separate from timeline.db."""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timezone


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS libraries (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS roots (
  id INTEGER PRIMARY KEY,
  library_id INTEGER NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  path_key TEXT NOT NULL,
  UNIQUE(library_id, path_key)
);
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY,
  library_id INTEGER NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  path_key TEXT NOT NULL,
  name TEXT NOT NULL,
  extension TEXT NOT NULL,
  size INTEGER NOT NULL,
  mtime REAL NOT NULL,
  ctime REAL NOT NULL,
  indexed_at REAL NOT NULL,
  UNIQUE(library_id, path_key)
);
CREATE INDEX IF NOT EXISTS files_name ON files(library_id, name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS files_extension ON files(library_id, extension);
CREATE INDEX IF NOT EXISTS roots_library ON roots(library_id);
"""


def path_key(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path))).casefold()


class LibraryStore:
    """Metadata-only library store. It never copies or edits source documents."""

    def __init__(self, path):
        self.path = os.fspath(path)
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=NORMAL")
            self._db.executescript(SCHEMA)

    def close(self):
        with self._lock:
            self._db.close()

    def create(self, name, description=""):
        name, description = str(name).strip(), str(description).strip()
        if not name or len(name) > 100 or len(description) > 1000:
            raise ValueError("자료함 이름은 1~100자, 설명은 1,000자 이내로 입력해 주세요.")
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO libraries(name,description,created_at) VALUES(?,?,?)",
                (name, description, datetime.now(timezone.utc).isoformat()),
            )
            return self.get(cur.lastrowid)

    def get(self, library_id):
        with self._lock:
            row = self._db.execute("SELECT * FROM libraries WHERE id=?", (int(library_id),)).fetchone()
        return dict(row) if row else None

    def list_libraries(self):
        with self._lock:
            rows = self._db.execute(
                "SELECT l.*, COUNT(DISTINCT r.id) roots, COUNT(DISTINCT f.id) files "
                "FROM libraries l LEFT JOIN roots r ON r.library_id=l.id "
                "LEFT JOIN files f ON f.library_id=l.id GROUP BY l.id ORDER BY l.id"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_root(self, library_id, path):
        key = path_key(path)
        with self._lock:
            if not self.get(library_id):
                raise ValueError("자료함을 찾을 수 없습니다.")
            self._db.execute("INSERT OR IGNORE INTO roots(library_id,path,path_key) VALUES(?,?,?)",
                             (int(library_id), os.path.abspath(path), key))
            row = self._db.execute("SELECT * FROM roots WHERE library_id=? AND path_key=?",
                                   (int(library_id), key)).fetchone()
        return dict(row)

    def roots(self, library_id):
        with self._lock:
            rows = self._db.execute("SELECT * FROM roots WHERE library_id=? ORDER BY id", (int(library_id),))
        return [dict(row) for row in rows]

    def upsert_files(self, library_id, files):
        now = datetime.now(timezone.utc).timestamp()
        values = []
        for item in files:
            path = os.path.abspath(item["path"])
            values.append((int(library_id), path, path_key(path), os.path.basename(path),
                           os.path.splitext(path)[1].lower(), int(item["size"]),
                           float(item["mtime"]), float(item["ctime"]), now))
        if not values:
            return 0
        with self._lock:
            self._db.execute("BEGIN")
            try:
                self._db.executemany(
                    "INSERT INTO files(library_id,path,path_key,name,extension,size,mtime,ctime,indexed_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(library_id,path_key) DO UPDATE SET "
                    "path=excluded.path,name=excluded.name,extension=excluded.extension,size=excluded.size,"
                    "mtime=excluded.mtime,ctime=excluded.ctime,indexed_at=excluded.indexed_at", values)
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise
        return len(values)

    def remove_missing(self, library_id, root, seen_paths):
        """Drop vanished entries under one fully scanned root; never touch source files."""
        root_key = path_key(root)
        seen = {path_key(path) for path in seen_paths}
        with self._lock:
            rows = self._db.execute("SELECT id,path,path_key FROM files WHERE library_id=?", (int(library_id),)).fetchall()
            remove = []
            for row in rows:
                try:
                    inside = os.path.commonpath((root_key, row["path_key"])) == root_key
                except ValueError:
                    inside = False
                if inside and row["path_key"] not in seen:
                    remove.append(row["id"])
            if remove:
                self._db.executemany("DELETE FROM files WHERE id=?", ((item,) for item in remove))
        return len(remove)

    def known_under(self, library_id, root):
        root_key = path_key(root)
        result = {}
        with self._lock:
            rows = self._db.execute("SELECT path,path_key,size,mtime,ctime FROM files WHERE library_id=?",
                                    (int(library_id),)).fetchall()
        for row in rows:
            try:
                inside = os.path.commonpath((root_key, row["path_key"])) == root_key
            except ValueError:
                inside = False
            if inside:
                result[row["path_key"]] = (row["size"], row["mtime"], row["ctime"])
        return result

    def search(self, library_id, query="", extensions=None, limit=200, offset=0):
        query = str(query).strip()
        if len(query) > 200:
            raise ValueError("검색어는 200자 이하로 입력해 주세요.")
        limit = max(1, min(int(limit), 1000))
        where, params = ["library_id=?"], [int(library_id)]
        if query:
            escaped = query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where.append("name LIKE ? ESCAPE '\\'")
            params.append(f"%{escaped}%")
        if extensions:
            normalized = [str(ext).lower() if str(ext).startswith(".") else "." + str(ext).lower()
                          for ext in extensions]
            if any(len(ext) > 16 or not ext[1:].isalnum() for ext in normalized):
                raise ValueError("파일 형식 필터를 확인해 주세요.")
            where.append("extension IN (" + ",".join("?" for _ in normalized) + ")")
            params.extend(normalized)
        with self._lock:
            rows = self._db.execute(
                f"SELECT id,path,name,extension,size,mtime,ctime FROM files WHERE {' AND '.join(where)} "
                "ORDER BY mtime DESC,name COLLATE NOCASE LIMIT ? OFFSET ?",
                [*params, limit, max(0, int(offset))]).fetchall()
        return [dict(row) for row in rows]

