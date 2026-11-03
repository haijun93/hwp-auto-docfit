"""별도 SQLite FTS5 문서 본문 색인 및 로컬 텍스트 추출."""
from __future__ import annotations

import os
import sqlite3
import threading
import re
from datetime import date
from pathlib import Path
from defusedxml import ElementTree as ET
from ..hwpx import open_hwpx_safely

SUPPORTED = {"hwpx", "txt", "docx", "pdf"}

# 종류 우선순위 순서: 명시 기준일 > 분기 > 반기
_DATE_PATTERNS = (
    # 월·일 뒤 (?!\d)로 숫자 경계를 지키고, 일이 숫자 경계에서 끊기면(예: 9. 301) 일 없는 해석으로 떨어지지 않게 한다.
    # 일치 원문에는 끝 표기(일·월·마침표)까지 포함한다.
    ("explicit", re.compile(r"(?:작성\s*)?기준일\s*[:：]?\s*(20\d{2})\s*[.년/-]\s*(\d{1,2})(?!\d)"
                            r"(?:\s*[.월/-]\s*(\d{1,2})(?!\d)(?:\s*일)?|(?!\s*[.월/-]\s*\d)(?:\s*월)?)(?:\s*\.)?")),
    ("quarter", re.compile(r"(20\d{2})\s*년도?\s*([1-4])\s*분기")),
    ("half", re.compile(r"(20\d{2})\s*년도?\s*(상|하)반기")),
)


def _match_date(source, match):
    """일치 하나를 날짜로 바꾼다. 잘못된 날짜면 ValueError."""
    year = int(match.group(1))
    if source == "explicit":
        day = match.group(3)
        return date(year, int(match.group(2)), int(day) if day else 1)
    if source == "quarter":
        return date(year, int(match.group(2)) * 3, 1)
    return date(year, 6 if match.group(2) == "상" else 12, 1)


def extract_reference_date_info(text):
    """본문에서 작성 기준일과 그 출처(explicit/quarter/half)를 찾는다.

    종류 우선(명시 기준일 > 분기 > 반기), 같은 종류는 본문에서 먼저 나온 것을 쓴다.
    잘못된 날짜(예: 2026.2.30)는 그 일치만 건너뛴다.
    """
    for source, pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text or ""):
            try:
                value = _match_date(source, match)
            except ValueError:
                continue
            return {"date": value.isoformat(), "source": source, "text": match.group(0).strip()}
    return {"date": None, "source": None, "text": None}


def extract_reference_date(text):
    """본문에서 작성 기준일 또는 연·분기/반기 기준일을 ISO 날짜로 돌려준다."""
    return extract_reference_date_info(text)["date"]


def extract_text(path):
    ext = Path(path).suffix.lower().lstrip(".")
    if ext not in SUPPORTED:
        raise ValueError("지원하지 않는 형식")
    if ext == "txt":
        raw = Path(path).read_bytes()
        for encoding in ("utf-8-sig", "cp949", "utf-16"):
            try:
                return raw.decode(encoding)
            except UnicodeError:
                pass
        raise ValueError("텍스트 인코딩을 판별할 수 없음")
    if ext in ("hwpx", "docx"):
        chunks = []
        opener = open_hwpx_safely if ext == "hwpx" else __import__("zipfile").ZipFile
        with opener(path) as archive:
            names = archive.namelist()
            if ext == "hwpx":
                targets = [n for n in names if n.startswith("Contents/section") and n.endswith(".xml")]
            else:
                targets = [n for n in names if n == "word/document.xml" or
                           (n.startswith("word/header") or n.startswith("word/footer")) and n.endswith(".xml")]
            for name in targets:
                root = ET.fromstring(archive.read(name))
                chunks.extend(t.strip() for t in root.itertext() if t and t.strip())
        text = "\n".join(chunks)
        if not text.strip():
            raise ValueError("본문 텍스트가 없음")
        return text
    from pypdf import PdfReader
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("암호화된 PDF")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not text.strip():
        raise ValueError("추출 가능한 PDF 텍스트가 없음")
    return text


class ContentSearchIndex:
    """메타데이터 DB와 물리적으로 분리된 FTS5 색인."""
    def __init__(self, path):
        self.path = os.fspath(path)
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.RLock()
        self._closed = False
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS content_meta(path TEXT PRIMARY KEY, size INTEGER, mtime REAL, reference_date TEXT);
            CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(path UNINDEXED, name UNINDEXED, body, tokenize='unicode61');
            CREATE TABLE IF NOT EXISTS content_errors(path TEXT PRIMARY KEY, reason TEXT, size INTEGER, mtime REAL);
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(content_meta)")}
        if "reference_date" not in columns:
            self.db.execute("ALTER TABLE content_meta ADD COLUMN reference_date TEXT")

    def close(self):
        with self._lock:
            if not self._closed:
                self.db.close()
                self._closed = True

    def index_file(self, path):
        path = os.path.abspath(os.fspath(path))
        stat = os.stat(path)
        try:
            body = extract_text(path)
            with self._lock:
                old = self.db.execute("SELECT size,mtime FROM content_meta WHERE path=?", (path,)).fetchone()
                if old and old["size"] == stat.st_size and old["mtime"] == stat.st_mtime:
                    return {"indexed": False, "error": None}
                with self.db:
                    self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                    self.db.execute("INSERT INTO content_fts(path,name,body) VALUES(?,?,?)", (path, os.path.basename(path), body))
                    self.db.execute("INSERT OR REPLACE INTO content_meta(path,size,mtime,reference_date) VALUES(?,?,?,?)",
                                    (path, stat.st_size, stat.st_mtime, extract_reference_date(body)))
                    self.db.execute("DELETE FROM content_errors WHERE path=?", (path,))
            return {"indexed": True, "error": None}
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            with self._lock:
                with self.db:
                    self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                    self.db.execute("DELETE FROM content_meta WHERE path=?", (path,))
                    self.db.execute("INSERT OR REPLACE INTO content_errors VALUES(?,?,?,?)",
                                    (path, reason, stat.st_size, stat.st_mtime))
            return {"indexed": False, "error": reason}

    def remove_file(self, path):
        path = os.path.abspath(os.fspath(path))
        with self._lock:
            with self.db:
                self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_meta WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_errors WHERE path=?", (path,))

    def indexed_paths(self, *, roots=None):
        """색인된 경로 목록. 전달된 루트 안의 문서만 돌려준다."""
        with self._lock:
            rows = self.db.execute("SELECT path FROM content_meta").fetchall()
        allowed = [os.path.normcase(os.path.abspath(root)) for root in roots] if roots else None
        return [os.path.abspath(row["path"]) for row in rows if allowed is None or any(
            os.path.commonpath((os.path.normcase(os.path.abspath(row["path"])), root)) == root
            for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(os.path.abspath(row["path"]))[0].casefold())]

    def search(self, query, *, roots=None, limit=100):
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ValueError("검색어는 1~200자로 입력해 주세요.")
        # 일반 문구는 FTS 구문이 아닌 안전한 phrase로 처리
        phrase = '"' + query.replace('"', '""') + '"'
        sql = "SELECT f.path,f.name,snippet(content_fts,2,'','','…',18) snippet FROM content_fts f WHERE content_fts MATCH ?"
        with self._lock:
            rows = self.db.execute(sql + " ORDER BY rank LIMIT ?", (phrase, max(1, min(int(limit), 500)))).fetchall()
        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        result = []
        for row in rows:
            path = os.path.abspath(row["path"])
            if any(part.casefold() == "$recycle.bin" for part in Path(path).parts):
                continue
            if allowed is not None and not any(os.path.commonpath((os.path.normcase(path), root)) == root
                                               for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(path)[0].casefold()):
                continue
            result.append({"path": path, "name": row["name"], "snippet": row["snippet"]})
        return result

    def errors(self, roots=None):
        with self._lock:
            rows = self.db.execute("SELECT path,reason FROM content_errors ORDER BY path").fetchall()
        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        return [dict(r) for r in rows if not any(p.casefold() == "$recycle.bin" for p in Path(r["path"]).parts)
                and (allowed is None or any(os.path.commonpath((os.path.normcase(os.path.abspath(r["path"])), root)) == root
                                            for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(os.path.abspath(r["path"]))[0].casefold()))]

    def related_candidates(self, path, roots=None):
        path = os.path.abspath(os.fspath(path))
        with self._lock:
            selected = self.db.execute("SELECT f.path,f.name,f.body,m.reference_date FROM content_fts f JOIN content_meta m ON m.path=f.path WHERE f.path=?", (path,)).fetchone()
            rows = self.db.execute("SELECT f.path,f.name,f.body,m.reference_date FROM content_fts f JOIN content_meta m ON m.path=f.path WHERE f.path<>?", (path,)).fetchall()
        if not selected:
            return None, []
        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        candidates = []
        for row in rows:
            item_path = os.path.normcase(os.path.abspath(row["path"]))
            if allowed is not None and not any(os.path.commonpath((item_path, root)) == root for root in allowed
                    if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(os.path.abspath(row["path"]))[0].casefold()):
                continue
            candidates.append(row)
        return selected, candidates
