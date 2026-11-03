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

_DATE_PATTERNS = (
    re.compile(r"(?:작성\s*)?기준일\s*[:：]?\s*(20\d{2})\s*[.년/-]\s*(\d{1,2})\s*[.월/-]\s*(\d{1,2})\s*일?"),
    re.compile(r"(20\d{2})\s*년도?\s*(\d{1,2})\s*분기"),
    re.compile(r"(?:작성\s*)?기준일\s*[:：]?\s*(20\d{2})\s*년?\s*(\d{1,2})\s*월?"),
    re.compile(r"(20\d{2})\s*년도?\s*(\d{1,2})\s*분기"),
)


def extract_reference_date(text):
    """본문에서 작성 기준일 또는 연·분기/연도 기준일을 ISO 날짜로 돌려준다."""
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            parts = [int(part) for part in match.groups()]
            try:
                if len(parts) == 3:
                    return date(*parts).isoformat()
                if len(parts) == 2 and "분기" in match.group(0):
                    year, quarter = parts
                    if 1 <= quarter <= 4:
                        return date(year, quarter * 3, 1).isoformat()
                if len(parts) == 3:
                    return date(*parts).isoformat()
                if len(parts) == 2:
                    return date(parts[0], parts[1], 1).isoformat()
            except ValueError:
                continue
    return None


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
            CREATE TABLE IF NOT EXISTS content_errors(path TEXT PRIMARY KEY, reason TEXT, size INTEGER, mtime REAL);
        """)
        # Keep the legacy table as migration source; trigram supports Korean substring matches.
        try:
            fts_exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE name='content_fts'").fetchone()
            if fts_exists:
                sql = self.db.execute("SELECT sql FROM sqlite_master WHERE name='content_fts'").fetchone()[0]
                if "trigram" not in (sql or "").lower():
                    with self.db:
                        self.db.execute("ALTER TABLE content_fts RENAME TO content_fts_legacy")
                        self.db.execute("CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body, tokenize='trigram')")
                        self.db.execute("INSERT INTO content_fts(path,name,body) SELECT path,name,body FROM content_fts_legacy")
                        self.db.execute("DROP TABLE content_fts_legacy")
            else:
                self.db.execute("CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body, tokenize='trigram')")
            cols = {r[1] for r in self.db.execute("PRAGMA table_info(content_meta)")}
            if "reference_date" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN reference_date TEXT")
            if "name" not in cols: self.db.execute("ALTER TABLE content_meta ADD COLUMN name TEXT")
            if "extension" not in cols: self.db.execute("ALTER TABLE content_meta ADD COLUMN extension TEXT")
            if "mtime" not in cols: self.db.execute("ALTER TABLE content_meta ADD COLUMN mtime REAL")
            if "size" not in cols: self.db.execute("ALTER TABLE content_meta ADD COLUMN size INTEGER")
            self.db.execute("UPDATE content_meta SET name=COALESCE(name,(SELECT name FROM content_fts WHERE content_fts.path=content_meta.path)), extension=COALESCE(extension,lower(substr(path,instr(path,'.')+1))), mtime=COALESCE(mtime,0), size=COALESCE(size,0)")
            with self.db:
                for row in self.db.execute("SELECT path,name,body FROM content_fts_legacy").fetchall():
                    self.db.execute("INSERT INTO content_fts(path,name,body) VALUES(?,?,?)", tuple(row))
                self.db.execute("DROP TABLE content_fts_legacy")
            self.migration_error = None
        except sqlite3.OperationalError as exc:
            # A legacy unicode61 table named content_fts needs a safe rebuild.
            try:
                with self.db:
                    self.db.execute("ALTER TABLE content_fts RENAME TO content_fts_legacy")
                    self.db.execute("CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body, tokenize='trigram')")
                    self.db.execute("INSERT INTO content_fts(path,name,body) SELECT path,name,body FROM content_fts_legacy")
                    self.db.execute("DROP TABLE content_fts_legacy")
                self.migration_error = None
            except sqlite3.Error as migration_exc:
                self.migration_error = str(migration_exc)
                raise RuntimeError("본문 색인 스키마 이전에 실패했습니다. 본문 재색인이 필요합니다.") from migration_exc

    @staticmethod
    def parse_query(query):
        """Parse AND terms, quoted phrases and Docufinder-style filters."""
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ValueError("검색어는 1~200자로 입력해 주세요.")
        tokens = re.findall(r'-?"(?:[^"\\]|\\.)*"|\S+', query)
        parsed = {"terms": [], "phrases": [], "exclude": [], "ext": [], "path": [], "after": None, "before": None, "near": None}
        for token in tokens:
            neg = token.startswith("-")
            raw = token[1:] if neg else token
            if raw.startswith('"') and raw.endswith('"'):
                parsed["exclude" if neg else "phrases"].append(raw[1:-1].replace('\\"','"'))
                continue
            if not neg and ":" in raw:
                key, value = raw.split(":", 1)
                if key == "ext": parsed["ext"].extend(x.lower().lstrip(".") for x in value.split(",") if x)
                elif key == "path" and value: parsed["path"].append(value)
                elif key in ("after", "before"):
                    parsed[key] = value if re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", value) else (_ for _ in ()).throw(ValueError(f"{key} 날짜 형식이 올바르지 않습니다."))
                else: parsed["terms"].append(raw)
                continue
            if not neg and re.fullmatch(r"~\d+", raw): parsed["near"] = int(raw[1:]); continue
            (parsed["exclude"] if neg else parsed["terms"]).append(raw)
        return parsed

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
                    self.db.execute("UPDATE content_meta SET name=?,extension=? WHERE path=?", (os.path.basename(path), Path(path).suffix.lower().lstrip("."), path))
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

    def search(self, query, *, roots=None, limit=100, sort="relevance"):
        parsed = self.parse_query(query)
        terms = parsed["terms"] + parsed["phrases"]
        if not terms:
            raise ValueError("본문 검색어를 입력해 주세요.")
        lim = max(1, min(int(limit), 500))
        # >=3 characters use indexed trigram; short Korean terms use substring scan.
        candidates = None
        short_terms = []
        for term in terms:
            if len(term) < 3:
                short_terms.append(term)
                continue
            try:
                with self._lock:
                    expression = '"' + term.replace('"','""') + '"'
                    found = {r[0] for r in self.db.execute("SELECT path FROM content_fts WHERE content_fts MATCH ?", (expression,))}
            except sqlite3.OperationalError:
                with self._lock:
                    found = {r[0] for r in self.db.execute("SELECT path FROM content_fts WHERE body LIKE ?", ("%" + term + "%",))}
            candidates = found if candidates is None else candidates & found
            if not candidates:
                return []
        with self._lock:
            if candidates is None:
                rows = self.db.execute("SELECT path,name,body FROM content_fts").fetchall()
            else:
                marks = ",".join("?" for _ in candidates)
                rows = self.db.execute(f"SELECT path,name,body FROM content_fts WHERE path IN ({marks})", tuple(candidates)).fetchall()
            reference_dates = {r["path"]: r["reference_date"] for r in self.db.execute("SELECT path,reference_date FROM content_meta")}
        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        result = []
        prepared = []
        for row in rows:
            path = os.path.abspath(row["path"])
            if any(part.casefold() == "$recycle.bin" for part in Path(path).parts):
                continue
            if allowed is not None and not any(os.path.commonpath((os.path.normcase(path), root)) == root
                                               for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(path)[0].casefold()):
                continue
            ext = Path(path).suffix.lower().lstrip(".")
            parent = os.path.dirname(path).casefold()
            if parsed["ext"] and ext not in parsed["ext"]: continue
            if parsed["path"] and not all(v.casefold() in path.casefold() for v in parsed["path"]): continue
            ref_date = reference_dates.get(row["path"])
            if parsed["after"] and (not ref_date or ref_date < parsed["after"]): continue
            if parsed["before"] and (not ref_date or ref_date >= parsed["before"]): continue
            body = row["body"] or ""
            folded = body.casefold()
            if any(t.casefold() not in folded for t in terms): continue
            if any(t.casefold() in folded for t in parsed["exclude"]): continue
            # N proximity: all terms must occur within N intervening whitespace tokens.
            if parsed["near"] is not None and len(terms) > 1:
                word_spans = [(m.group().casefold(), m.start(), m.end()) for m in re.finditer(r"\S+", body)]
                term_positions = [[i for i, (word, _, _) in enumerate(word_spans) if term.casefold() in word]
                                  for term in terms]
                if any(not p for p in term_positions): continue
                if not any(max(combo) - min(combo) <= parsed["near"] + 1
                           for combo in __import__('itertools').product(*term_positions)):
                    continue
            offsets = [folded.find(t.casefold()) for t in terms if folded.find(t.casefold()) >= 0]
            first = min(offsets) if offsets else 0
            start, end = max(0, first - 70), min(len(body), first + 180)
            snippet = body[start:end]
            spans = []
            for term in terms:
                match = re.search(re.escape(term), snippet, re.I)
                if match: spans.append([match.start(), match.end()])
            # Count positive terms only; phrases are counted as whole phrases.
            count_terms = [(t, t) for t in parsed["terms"]] + [(p, p) for p in parsed["phrases"]]
            match_counts = {label: folded.count(term.casefold()) for label, term in count_terms}
            score = sum(match_counts.values())
            total_matches = score
            result.append({"path": path, "name": row["name"], "snippet": snippet, "highlights": spans,
                           "score": score, "match_counts": match_counts, "total_matches": total_matches,
                           "position": {"page": None, "sheet": None, "row": None}})
        if sort == "mentions":
            result.sort(key=lambda item: (-item["total_matches"], item["name"].casefold()))
        else:
            result.sort(key=lambda item: (-item["score"], item["name"].casefold()))
        return result[:lim]

    def search_files(self, query, *, roots=None, limit=500):
        """Immediate in-memory filename cache populated from indexed metadata."""
        words = [w.casefold() for w in query.split() if w]
        if not words: return []
        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        with self._lock: rows = self.db.execute("SELECT path,name,size,mtime,extension FROM content_meta ORDER BY name COLLATE NOCASE").fetchall()
        out = []
        for r in rows:
            p = os.path.abspath(r["path"])
            if all(w in r["name"].casefold() for w in words) and (allowed is None or any(os.path.commonpath((os.path.normcase(p), root)) == root for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(p)[0].casefold())):
                out.append({"path": p, "name": r["name"] or Path(p).name, "size": r["size"], "mtime": r["mtime"], "extension": r["extension"] or Path(p).suffix.lower().lstrip(".")})
                if len(out) >= limit: break
        return out

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
            selected = self.db.execute("SELECT f.body,m.reference_date FROM content_fts f JOIN content_meta m ON m.path=f.path WHERE f.path=?", (path,)).fetchone()
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
