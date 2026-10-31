"""타임머신 색인(SQLite). 파일 메타데이터만 저장하고 작업 시각 구간·일별 집계를 빠르게 돌려준다."""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    root TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    ctime REAL NOT NULL,
    work_time REAL NOT NULL,
    flags TEXT NOT NULL DEFAULT '',
    cloud INTEGER NOT NULL DEFAULT 0,
    hidden INTEGER NOT NULL DEFAULT 0,
    seen INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS files_work_time ON files(work_time);
CREATE INDEX IF NOT EXISTS files_root ON files(root);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""
MAX_PAGE = 2000


def path_key(path):
    return os.path.normcase(os.path.normpath(path)).casefold()


class Store:
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
            self._db.execute("PRAGMA cache_size=-2000")  # 약 2MB
            self._db.executescript(SCHEMA)

    def close(self):
        with self._lock:
            self._db.close()

    # ── 쓰기(스캐너) ─────────────────────────────────────────────────────
    def known(self, root):
        """root 아래 색인된 파일: key → (size, mtime, ctime)."""
        with self._lock:
            rows = self._db.execute("SELECT key, size, mtime, ctime FROM files WHERE root = ?", (path_key(root),))
            return {row["key"]: (row["size"], row["mtime"], row["ctime"]) for row in rows}

    def upsert_many(self, rows):
        """rows: dict(path, root, name, kind, size, mtime, ctime, work_time, flags, cloud). 쓴 개수."""
        if not rows:
            return 0
        with self._lock:
            self._db.execute("BEGIN")
            try:
                self._db.executemany(
                    "INSERT INTO files(key, path, root, name, kind, size, mtime, ctime, work_time, flags, cloud) "
                    "VALUES(:key, :path, :root, :name, :kind, :size, :mtime, :ctime, :work_time, :flags, :cloud) "
                    "ON CONFLICT(key) DO UPDATE SET path=excluded.path, name=excluded.name, kind=excluded.kind, "
                    "size=excluded.size, mtime=excluded.mtime, ctime=excluded.ctime, work_time=excluded.work_time, "
                    "flags=excluded.flags, cloud=excluded.cloud",
                    [dict(row, key=path_key(row["path"]), root=path_key(row["root"]), flags=",".join(row["flags"]),
                          cloud=int(bool(row.get("cloud")))) for row in rows])
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise
        return len(rows)

    def delete_keys(self, keys):
        keys = list(keys)
        with self._lock:
            self._db.execute("BEGIN")
            for start in range(0, len(keys), 500):
                chunk = keys[start:start + 500]
                self._db.execute(f"DELETE FROM files WHERE key IN ({','.join('?' * len(chunk))})", chunk)
            self._db.execute("COMMIT")
        return len(keys)

    def drop_root(self, root):
        with self._lock:
            return self._db.execute("DELETE FROM files WHERE root = ?", (path_key(root),)).rowcount

    def clear(self):
        with self._lock:
            self._db.execute("DELETE FROM files")
            self._db.execute("VACUUM")

    def hide(self, file_id, hidden=True):
        with self._lock:
            return self._db.execute("UPDATE files SET hidden = ? WHERE id = ?", (int(hidden), file_id)).rowcount == 1

    # ── 읽기(화면) ───────────────────────────────────────────────────────
    @staticmethod
    def _filters(kinds=None, roots=None, query=None):
        where, params = ["hidden = 0"], []
        if kinds:
            where.append(f"kind IN ({','.join('?' * len(kinds))})")
            params.extend(kinds)
        if roots:
            where.append(f"root IN ({','.join('?' * len(roots))})")
            params.extend(path_key(r) for r in roots)
        if query:
            escaped = query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where.append("lower(name) LIKE ? ESCAPE '\\'")
            params.append(f"%{escaped}%")
        return where, params

    def range(self, start, end, *, kinds=None, roots=None, query=None, newest_first=True, limit=200, offset=0):
        """[start, end) 구간(유닉스 초)의 파일. 가상 스크롤용으로 limit·offset."""
        limit = max(1, min(int(limit), MAX_PAGE))
        where, params = self._filters(kinds, roots, query)
        where.insert(0, "work_time >= ? AND work_time < ?")
        params[:0] = [start, end]
        order = "DESC" if newest_first else "ASC"
        sql = (f"SELECT id, path, name, kind, size, mtime, ctime, work_time, flags, cloud FROM files "
               f"WHERE {' AND '.join(where)} ORDER BY work_time {order}, id {order} LIMIT ? OFFSET ?")
        with self._lock:
            rows = self._db.execute(sql, [*params, limit, max(0, int(offset))]).fetchall()
        return [dict(row, flags=[f for f in row["flags"].split(",") if f], cloud=bool(row["cloud"])) for row in rows]

    def count(self, start, end, **filters):
        where, params = self._filters(**filters)
        with self._lock:
            return self._db.execute(f"SELECT COUNT(*) FROM files WHERE work_time >= ? AND work_time < ? AND "
                                    f"{' AND '.join(where)}", [start, end, *params]).fetchone()[0]

    def day_counts(self, year, month, **filters):
        """그 달 날짜별 파일 수(지역 시각 기준) {일: {kind: 수, 'total': 수}}. 달력 히트맵용."""
        first = datetime(year, month, 1)
        after = (first + timedelta(days=32)).replace(day=1)
        where, params = self._filters(**filters)
        sql = (f"SELECT CAST(strftime('%d', work_time, 'unixepoch', 'localtime') AS INTEGER) AS day, kind, COUNT(*) "
               f"FROM files WHERE work_time >= ? AND work_time < ? AND {' AND '.join(where)} GROUP BY day, kind")
        result = {}
        with self._lock:
            for day, kind, count in self._db.execute(sql, [first.timestamp(), after.timestamp(), *params]):
                bucket = result.setdefault(day, {"total": 0})
                bucket[kind] = count
                bucket["total"] += count
        return result

    def hour_density(self, start, end, **filters):
        """구간 안 시간대(0~23)별 파일 수 — 타임라인 옆 활동 밀도 막대."""
        where, params = self._filters(**filters)
        sql = (f"SELECT CAST(strftime('%H', work_time, 'unixepoch', 'localtime') AS INTEGER), COUNT(*) FROM files "
               f"WHERE work_time >= ? AND work_time < ? AND {' AND '.join(where)} GROUP BY 1")
        with self._lock:
            return {hour: count for hour, count in self._db.execute(sql, [start, end, *params])}

    def get(self, file_id):
        with self._lock:
            row = self._db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        return dict(row) if row else None

    def stats(self):
        with self._lock:
            row = self._db.execute("SELECT COUNT(*), MIN(work_time), MAX(work_time) FROM files WHERE hidden = 0"
                                   ).fetchone()
        return dict(files=row[0], first=row[1], last=row[2])
