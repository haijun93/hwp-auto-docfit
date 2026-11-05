"""별도 SQLite FTS5 문서 본문 색인 및 로컬 텍스트 추출."""
from __future__ import annotations

import os
import sqlite3
import threading
from .rules import excluded_name
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from defusedxml import ElementTree as ET
from ..hwpx import open_hwpx_safely
from .extract_text import extract_text as _extract_text_by_format
from .extractors import ExtractionError, extract_document

SUPPORTED = {"hwpx", "hwp", "txt", "md", "docx", "pptx", "xlsx", "xls", "pdf", "eml"}

LEVEL_ORDER: tuple[str, ...] = (
    "document_title", "chapter", "section", "topic", "square", "circle",
    "dash", "asterisk", "body",
)
LEVEL_RANKS: dict[str, int] = {level: rank for rank, level in enumerate(LEVEL_ORDER)}
# 표 칸은 표시 이름을 유지하면서 본문과 같은 최하위 위계를 사용한다.
LEVEL_RANKS["table_cell"] = LEVEL_RANKS["body"]
LEVEL_LABELS: dict[str, str] = {
    "document_title": "문서 제목", "chapter": "장", "section": "절",
    "topic": "주제·소제목", "square": "ㅁ", "circle": "ㅇ",
    "dash": "-", "asterisk": "*", "body": "본문", "table_cell": "표 칸",
}
ROLE_TO_LEVEL: dict[str, str] = {
    "장": "chapter",
    "중제목": "section",
    "소제목": "topic",
    "본문": "body",
    "내용": "body",
    "부연설명": "asterisk",
}
MARKER_CLASS_TO_LEVEL: dict[str, str] = {
    "□": "square",
    "ㅁ": "square",
    "■": "square",
    "ㅇ": "circle",
    "○": "circle",
    "◦": "circle",
    "-": "dash",
    "*": "asterisk",
    "**": "asterisk",
    "※": "asterisk",
    "•": "asterisk",
    "·": "asterisk",
    "‧": "asterisk",
    "∙": "asterisk",
    "⋅": "asterisk",
    "ㆍ": "asterisk",
    "●": "asterisk",
    "・": "asterisk",
    "–": "dash",
    "—": "dash",
    "−": "dash",
    "－": "dash",
}
CURRENT_HIERARCHY_SCHEMA_VERSION = 1
_EXTRACTED_LOCATIONS: dict[str, dict[int, tuple[str, str | None]]] = {}
_EXTRACTED_LOCATIONS_LOCK = threading.RLock()


def _terms_are_near(text: str, terms: list[str], distance: int) -> bool:
    words = [match.group().casefold() for match in re.finditer(r"\S+", text)]
    positions = [[index for index, word in enumerate(words) if term.casefold() in word] for term in terms]
    if any(not found for found in positions):
        return False
    import itertools
    return any(max(combo) - min(combo) <= distance + 1 for combo in itertools.product(*positions))


@dataclass(frozen=True)
class ParagraphRecord:
    paragraph_index: int
    text: str
    level: str
    level_rank: int
    is_table_cell: bool
    style_name: str | None = None
    outline_level: int | None = None


@dataclass
class ParagraphMatch:
    paragraph_index: int
    level: str
    level_rank: int
    match_counts: dict[str, int]
    bm25: float
    snippet: str
    highlights: list[list[int]]


def _tag_name(elem) -> str:
    tag = elem.tag
    return tag.split("}")[-1] if "}" in tag else tag


def _best_level(matches: list[ParagraphMatch]) -> tuple[str, int]:
    if not matches:
        body_rank = LEVEL_ORDER.index("body")
        return LEVEL_LABELS["body"], body_rank
    best = min(matches, key=lambda m: m.level_rank)
    return LEVEL_LABELS.get(best.level, LEVEL_LABELS["body"]), best.level_rank


def _document_date(created_at: float | None, modified_at: float | None) -> float:
    c = created_at if (isinstance(created_at, (int, float)) and created_at > 0) else 0.0
    m = modified_at if (isinstance(modified_at, (int, float)) and modified_at > 0) else 0.0
    return max(c, m)


def _sort_hierarchy_results(items: list[dict], *, sort: str) -> None:
    if sort == "hierarchy_relevance":
        def key_fn(item):
            best_rank = item.get("_best_level_rank", LEVEL_ORDER.index("body"))
            total = item.get("total_matches", 0)
            doc_date = item.get("_document_date", 0.0)
            has_date = 0 if doc_date > 0 else 1
            bm25 = item.get("_bm25_score", 0.0)
            path_norm = os.path.normcase(os.path.abspath(item["path"])).casefold()
            return (best_rank, -total, has_date, -doc_date, bm25, path_norm)
        items.sort(key=key_fn)
    elif sort == "mentions":
        items.sort(key=lambda item: (-item.get("total_matches", 0), item.get("name", "").casefold()))
    elif sort == "relevance":
        items.sort(key=lambda item: (-item.get("score", 0), item.get("name", "").casefold()))
    else:
        items.sort(key=lambda item: (-item.get("score", 0), item.get("name", "").casefold()))


def classify_paragraph_levels(path: str | os.PathLike[str], paragraphs: list[ParagraphRecord]) -> list[ParagraphRecord]:
    if not paragraphs:
        return []
    from ..style_hierarchy import leading_marker, canonical_marker, DOT_MARKERS
    from ..marker_scheme import detect_scheme, classify_marker
    from ..style_unify import unify_marker

    texts = [p.text for p in paragraphs]
    scheme = detect_scheme(texts)

    classified: list[ParagraphRecord] = []
    for p in paragraphs:
        text = p.text.strip()
        style_name = (p.style_name or "").lower()
        outline_lvl = p.outline_level
        level = None

        # [지적 4 반영] 표 셀 문단은 표 셀 예외를 최우선으로 적용하여 최하위인 table_cell로 고정
        if p.is_table_cell:
            level = "table_cell"
        else:
            # 1. HWPX 명시 제목/heading 스타일과 outline level
            if any(w in style_name for w in ("문서제목", "문서 제목", "title")) or style_name == "제목" or outline_lvl == 0:
                level = "document_title"
            elif any(w in style_name for w in ("heading 1", "개요 1", "개요1")) or outline_lvl == 1:
                level = "chapter"
            elif any(w in style_name for w in ("heading 2", "개요 2", "개요2")) or outline_lvl == 2:
                level = "section"
            elif any(w in style_name for w in ("heading 3", "개요 3", "개요3")) or outline_lvl == 3:
                level = "topic"

            if level is None:
                # [지적 3 반영] 저장소의 기존 기호 위계 판정 코드(leading_marker, unify_marker) 재사용 및 직접 매핑
                marker, role = leading_marker(text, scheme)
                unify_class, unify_role, raw_marker = unify_marker(text)

                canon_marker = canonical_marker(marker) if marker else ""
                canon_raw = canonical_marker(raw_marker) if raw_marker else ""
                cm = classify_marker(text)
                classified_marker = cm[0] if cm else ""
                canonical_classified_marker = canonical_marker(classified_marker) if classified_marker else ""
                effective_class = (
                    unify_class or canon_marker or canon_raw or canonical_classified_marker
                )

                # 기호 분류(MARKER_CLASS_TO_LEVEL) 우선 직접 매핑
                if effective_class in MARKER_CLASS_TO_LEVEL:
                    level = MARKER_CLASS_TO_LEVEL[effective_class]
                elif canon_marker in MARKER_CLASS_TO_LEVEL:
                    level = MARKER_CLASS_TO_LEVEL[canon_marker]
                elif canon_raw in MARKER_CLASS_TO_LEVEL:
                    level = MARKER_CLASS_TO_LEVEL[canon_raw]
                elif (raw_marker and raw_marker in DOT_MARKERS) or (marker and marker in DOT_MARKERS):
                    level = "asterisk"
                else:
                    # 역할(ROLE_TO_LEVEL) 기반 매핑
                    effective_role = role or unify_role

                    cm_family = cm[0] if cm else None
                    is_numbered_marker = bool(
                        cm_family
                        and (
                            cm_family.startswith("1")
                            or "가" in cm_family
                            or cm_family in ("①", "㉠", "㉮")
                        )
                    )
                    is_scheme_recognized = bool(
                        scheme
                        and (
                            scheme.canonical(text) is not None
                            or (cm_family and cm_family in scheme.family_levels)
                        )
                    )

                    if effective_role in ROLE_TO_LEVEL:
                        mapped_level = ROLE_TO_LEVEL[effective_role]
                        # 문맥 없는 단독 번호 기호는 body로 안전하게 처리 (문맥 체계에서 인정된 경우에만 절/주제 인정)
                        if is_numbered_marker and not is_scheme_recognized and mapped_level in ("section", "topic"):
                            level = "body"
                        else:
                            level = mapped_level
                    else:
                        level = "body"

        if level not in LEVEL_ORDER:
            level = "table_cell" if p.is_table_cell else "body"

        classified.append(
            ParagraphRecord(
                paragraph_index=p.paragraph_index,
                text=p.text,
                level=level,
                level_rank=LEVEL_RANKS[level],
                is_table_cell=p.is_table_cell,
                style_name=p.style_name,
                outline_level=p.outline_level,
            )
        )
    return classified


def extract_paragraphs(path: str | os.PathLike[str]) -> list[ParagraphRecord]:
    ext = Path(path).suffix.lower().lstrip(".")
    if ext not in SUPPORTED:
        raise ValueError("지원하지 않는 형식")
    if ext in {"hwpx", "docx"}:
        hierarchy_records = extract_paragraphs_legacy(path, ext)
    else:
        hierarchy_records = None
    try:
        extracted = extract_document(path, hierarchy_records=hierarchy_records)
    except ExtractionError as exc:
        raise ValueError(str(exc)) from exc
    with _EXTRACTED_LOCATIONS_LOCK:
        _EXTRACTED_LOCATIONS[os.path.abspath(os.fspath(path))] = {
            record.sequence - 1: (record.location_label, record.section) for record in extracted}
    paragraphs = [ParagraphRecord(
        paragraph_index=record.sequence - 1,
        text=record.text,
        level=record.hierarchy_level or "body",
        level_rank=LEVEL_RANKS.get(record.hierarchy_level, LEVEL_RANKS["body"]),
        is_table_cell=record.is_table_cell,
        style_name=record.style_name,
        outline_level=record.outline_level,
    ) for record in extracted]
    return classify_paragraph_levels(path, paragraphs)

def extract_paragraphs_legacy(path, ext):
    """위치 추출 전에 기존 HWPX/DOCX 위계 판정 결과를 얻는다."""
    records = []
    if ext == "hwpx":
        with open_hwpx_safely(path) as archive:
            names = archive.namelist()
            style_map = {}
            if "Contents/header.xml" in names:
                try:
                    head_root = ET.fromstring(archive.read("Contents/header.xml"))
                    for elem in head_root.iter():
                        if _tag_name(elem) == "style":
                            sid, sname = elem.attrib.get("id"), elem.attrib.get("name")
                            if sid and sname:
                                style_map[sid] = sname
                except Exception:
                    pass
            section_names = sorted((n for n in names if n.startswith("Contents/section") and n.endswith(".xml")),
                                   key=lambda n: int(re.search(r"section(\d+)", n).group(1)) if re.search(r"section(\d+)", n) else 0)
            index = 0
            def walk(node, in_table=False):
                nonlocal index
                tag = _tag_name(node)
                if tag in ("tc", "cell"):
                    for child in node:
                        walk(child, True)
                    return
                if tag == "p":
                    chunks = []
                    def collect(elem, root=False):
                        if not root and _tag_name(elem) in ("tbl", "table"):
                            return
                        if elem.text:
                            chunks.append(elem.text)
                        for child in elem:
                            collect(child)
                            if child.tail:
                                chunks.append(child.tail)
                    collect(node, True)
                    text = "".join(chunks).strip()
                    if text:
                        style_id = node.attrib.get("styleIDRef") or node.attrib.get("styleID") or node.attrib.get("style")
                        outline = node.attrib.get("outlineLevel") or node.attrib.get("outline_level")
                        for child in node:
                            if _tag_name(child) in ("pPr", "p_pr"):
                                style_id = style_id or child.attrib.get("styleIDRef") or child.attrib.get("styleID")
                                outline = outline or child.attrib.get("outlineLevel") or child.attrib.get("outline_level")
                        records.append(ParagraphRecord(index, text, "body", LEVEL_ORDER.index("body"), in_table,
                            style_map.get(style_id) if style_id else node.attrib.get("styleName"),
                            int(outline) if outline and outline.isdigit() else None))
                        index += 1
                    for child in node:
                        walk(child, in_table)
                    return
                for child in node:
                    walk(child, in_table)
            for name in section_names:
                walk(ET.fromstring(archive.read(name)))
    elif ext == "docx":
        with __import__("zipfile").ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                return []
            root = ET.fromstring(archive.read("word/document.xml"))
            index = 0
            def walk(node, in_table=False):
                nonlocal index
                tag = _tag_name(node)
                if tag == "tc":
                    for child in node:
                        walk(child, True)
                    return
                if tag == "p":
                    chunks = []
                    def collect(elem, root=False):
                        if not root and _tag_name(elem) in ("tbl", "table"):
                            return
                        if elem.text: chunks.append(elem.text)
                        for child in elem:
                            collect(child)
                            if child.tail: chunks.append(child.tail)
                    collect(node, True)
                    text = "".join(chunks).strip()
                    if text:
                        style = None; outline = None
                        for ppr in node:
                            if _tag_name(ppr) == "pPr":
                                for child in ppr:
                                    if _tag_name(child) == "pStyle": style = next(iter(child.attrib.values()), None)
                                    if _tag_name(child) == "outlineLvl":
                                        value = next(iter(child.attrib.values()), None)
                                        outline = int(value) if value and value.isdigit() else None
                        records.append(ParagraphRecord(index, text, "body", LEVEL_ORDER.index("body"), in_table, style, outline))
                        index += 1
                    for child in node:
                        walk(child, in_table)
                    return
                for child in node:
                    walk(child, in_table)
            walk(root)
    return classify_paragraph_levels(path, records)

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
    """?? ?? ??; ??? ?? ???? ????."""
    ext = Path(path).suffix.lower().lstrip(".")
    if ext not in SUPPORTED:
        raise ValueError("???? ?? ??")
    try:
        return _extract_text_by_format(path)
    except ExtractionError as exc:
        raise ValueError(str(exc)) from exc


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
            CREATE TABLE IF NOT EXISTS content_meta(
                path TEXT PRIMARY KEY,
                size INTEGER,
                mtime REAL,
                reference_date TEXT,
                name TEXT,
                extension TEXT,
                ctime REAL,
                hierarchy_schema_version INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS content_errors(path TEXT PRIMARY KEY, reason TEXT, size INTEGER, mtime REAL);
        """)
        self._paragraph_has_location = False
        try:
            # 1. 문단 FTS5 테이블 확인 및 생성
            para_exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE name='content_paragraph_fts'").fetchone()
            if para_exists:
                para_sql = (self.db.execute("SELECT sql FROM sqlite_master WHERE name='content_paragraph_fts'").fetchone() or [""])[0] or ""
                if "location_label" not in para_sql:
                    with self.db:
                        self.db.execute("ALTER TABLE content_paragraph_fts RENAME TO content_paragraph_fts_legacy")
                        self.db.execute("CREATE VIRTUAL TABLE content_paragraph_fts USING fts5(path UNINDEXED,name UNINDEXED,paragraph_index UNINDEXED,level UNINDEXED,level_rank UNINDEXED,body,location_label UNINDEXED,section UNINDEXED,tokenize='trigram')")
                        self.db.execute("INSERT INTO content_paragraph_fts(path,name,paragraph_index,level,level_rank,body,location_label,section) SELECT path,name,paragraph_index,level,level_rank,body,'문단 '||CAST(CAST(paragraph_index AS INTEGER)+1 AS TEXT),NULL FROM content_paragraph_fts_legacy")
                        self.db.execute("DROP TABLE content_paragraph_fts_legacy")
            else:
                self.db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS content_paragraph_fts USING fts5(
                    path UNINDEXED,
                    name UNINDEXED,
                    paragraph_index UNINDEXED,
                    level UNINDEXED,
                    level_rank UNINDEXED,
                    body,
                    location_label UNINDEXED,
                    section UNINDEXED,
                    tokenize='trigram'
                )
            """)
            self._paragraph_has_location = True
            # 2. 문서 FTS5 테이블 확인 및 생성/이전
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

            # SQLite trigram tokenizer cannot answer LIKE queries shorter than 3 chars.
            # Store distinct 2-character substrings as an ordinary indexed candidate table.
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS content_short_grams(
                    gram TEXT NOT NULL, path TEXT NOT NULL,
                    PRIMARY KEY(gram,path)
                );
                CREATE INDEX IF NOT EXISTS content_short_grams_path ON content_short_grams(path);
            """)

            cols = {r[1] for r in self.db.execute("PRAGMA table_info(content_meta)")}
            if "reference_date" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN reference_date TEXT")
            if "name" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN name TEXT")
            if "extension" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN extension TEXT")
            if "mtime" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN mtime REAL")
            if "size" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN size INTEGER")
            if "ctime" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN ctime REAL")
            if "hierarchy_schema_version" not in cols:
                self.db.execute("ALTER TABLE content_meta ADD COLUMN hierarchy_schema_version INTEGER NOT NULL DEFAULT 0")

            self.db.execute("""
                UPDATE content_meta
                SET name=COALESCE(name,(SELECT name FROM content_fts WHERE content_fts.path=content_meta.path)),
                    extension=COALESCE(extension,lower(substr(path,instr(path,'.')+1))),
                    mtime=COALESCE(mtime,0),
                    size=COALESCE(size,0),
                    ctime=COALESCE(ctime,0),
                    hierarchy_schema_version=COALESCE(hierarchy_schema_version,0)
            """)
            self.migration_error = None
        except sqlite3.OperationalError as exc:
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

    def needs_reindex_count(self, roots=None) -> int:
        """위계 정보가 없거나 오래된 스키마 버전의 색인 문서 수."""
        with self._lock:
            rows = self.db.execute("""
                SELECT m.path, m.hierarchy_schema_version,
                       (SELECT COUNT(*) FROM content_paragraph_fts p WHERE p.path = m.path) AS para_count
                FROM content_meta m
            """).fetchall()
        allowed = [os.path.normcase(os.path.abspath(root)) for root in roots] if roots else None
        count = 0
        for r in rows:
            path = os.path.abspath(r["path"])
            if allowed is not None and not any(
                os.path.commonpath((os.path.normcase(path), root)) == root
                for root in allowed
                if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(path)[0].casefold()
            ):
                continue
            if (r["hierarchy_schema_version"] or 0) < CURRENT_HIERARCHY_SCHEMA_VERSION or (r["para_count"] or 0) == 0:
                count += 1
        return count

    def index_file(self, path):
        path = os.path.abspath(os.fspath(path))
        from .rules import excluded_name
        if excluded_name(os.path.basename(path)):
            self.remove_file(path)
            return {"indexed": False, "error": None}
        stat = os.stat(path)
        ctime = getattr(stat, "st_ctime", 0.0)
        mtime = stat.st_mtime
        size = stat.st_size
        try:
            with self._lock:
                old = self.db.execute(
                    "SELECT size, mtime, hierarchy_schema_version FROM content_meta WHERE path=?",
                    (path,)
                ).fetchone()
                if (
                    old
                    and old["size"] == size
                    and old["mtime"] == mtime
                    and (old["hierarchy_schema_version"] or 0) >= CURRENT_HIERARCHY_SCHEMA_VERSION
                ):
                    has_para = self.db.execute("SELECT 1 FROM content_paragraph_fts WHERE path=? LIMIT 1", (path,)).fetchone()
                    if has_para:
                        return {"indexed": False, "error": None}

            paragraphs = extract_paragraphs(path)
            if not paragraphs:
                raise ValueError("본문 텍스트가 없음")
            body = "\n".join(p.text for p in paragraphs)
            ref_date = extract_reference_date(body)
            name = os.path.basename(path)
            ext = Path(path).suffix.lower().lstrip(".")

            with self._lock, self.db:
                self.db.execute("DELETE FROM content_paragraph_fts WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_short_grams WHERE path=?", (path,))
                for p in paragraphs:
                    location = _EXTRACTED_LOCATIONS.get(path, {}).get(p.paragraph_index,
                        (f"문단 {p.paragraph_index + 1}", None))
                    self.db.execute(
                        "INSERT INTO content_paragraph_fts(path, name, paragraph_index, level, level_rank, body, location_label, section) VALUES(?,?,?,?,?,?,?,?)",
                        (path, name, int(p.paragraph_index), p.level, int(p.level_rank), p.text, *location)
                    )
                self.db.execute("INSERT INTO content_fts(path, name, body) VALUES(?,?,?)", (path, name, body))
                grams = {body[i:i + 2].casefold() for i in range(max(0, len(body) - 1))}
                self.db.executemany("INSERT INTO content_short_grams(gram,path) VALUES(?,?)",
                                    ((gram, path) for gram in grams))
                self.db.execute(
                    "INSERT OR REPLACE INTO content_meta(path, size, mtime, ctime, reference_date, name, extension, hierarchy_schema_version) VALUES(?,?,?,?,?,?,?,?)",
                    (path, size, mtime, ctime, ref_date, name, ext, CURRENT_HIERARCHY_SCHEMA_VERSION)
                )
                self.db.execute("DELETE FROM content_errors WHERE path=?", (path,))
            return {"indexed": True, "error": None}
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            with self._lock, self.db:
                self.db.execute("DELETE FROM content_paragraph_fts WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                self.db.execute("DELETE FROM content_meta WHERE path=?", (path,))
                self.db.execute("INSERT OR REPLACE INTO content_errors VALUES(?,?,?,?)", (path, reason, size, mtime))
            return {"indexed": False, "error": reason}

    def remove_file(self, path):
        path = os.path.abspath(os.fspath(path))
        with self._lock, self.db:
            self.db.execute("DELETE FROM content_paragraph_fts WHERE path=?", (path,))
            self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
            self.db.execute("DELETE FROM content_short_grams WHERE path=?", (path,))
            self.db.execute("DELETE FROM content_meta WHERE path=?", (path,))
            self.db.execute("DELETE FROM content_errors WHERE path=?", (path,))

    def indexed_paths(self, *, roots=None):
        """색인된 경로 목록. 전달된 루트 안의 문서만 돌려준다."""
        with self._lock:
            rows = self.db.execute("SELECT path FROM content_meta").fetchall()
            bad = [row["path"] for row in rows if excluded_name(os.path.basename(row["path"]))]
            if bad:
                with self.db:
                    for path in bad:
                        self.db.execute("DELETE FROM content_paragraph_fts WHERE path=?", (path,))
                        self.db.execute("DELETE FROM content_fts WHERE path=?", (path,))
                        self.db.execute("DELETE FROM content_short_grams WHERE path=?", (path,))
                        self.db.execute("DELETE FROM content_meta WHERE path=?", (path,))
                        self.db.execute("DELETE FROM content_errors WHERE path=?", (path,))
                rows = [row for row in rows if row["path"] not in set(bad)]
        allowed = [os.path.normcase(os.path.abspath(root)) for root in roots] if roots else None
        return [os.path.abspath(row["path"]) for row in rows if not excluded_name(os.path.basename(row["path"])) and (allowed is None or any(
            os.path.commonpath((os.path.normcase(os.path.abspath(row["path"])), root)) == root
            for root in allowed if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(os.path.abspath(row["path"]))[0].casefold()))]

    def search(self, query, *, roots=None, limit=100, sort="hierarchy_relevance"):
        parsed = self.parse_query(query)
        terms = parsed["terms"] + parsed["phrases"]
        if not terms:
            raise ValueError("본문 검색어를 입력해 주세요.")
        lim = max(1, min(int(limit), 500))

        # 1. Trigram 전문 검색으로 양성 검색어별 후보 경로 추출 (AND 교집합)
        candidates = None
        fts_terms = [t for t in terms if len(t) >= 3]
        for term in fts_terms:
            expression = '"' + term.replace('"', '""') + '"'
            try:
                with self._lock:
                    found = {r[0] for r in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE content_paragraph_fts MATCH ?", (expression,))}
            except sqlite3.OperationalError:
                with self._lock:
                    found = {r[0] for r in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + term + "%",))}
            candidates = found if candidates is None else candidates & found
            if not candidates:
                return []

        if candidates is None:
            # 2글자 이하 검색어: LIKE로 후보 경로 조회
            for term in terms:
                with self._lock:
                    found = {r[0] for r in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + term + "%",))}
                candidates = found if candidates is None else candidates & found
                if not candidates:
                    return []

        # 2. 메타데이터 조회 및 필터링 (구형 스키마 버전 문서는 제외)
        with self._lock:
            if len(candidates) <= 500:
                marks = ",".join("?" for _ in candidates)
                meta_rows = self.db.execute(f"""
                    SELECT path, name, extension, mtime, ctime, reference_date, hierarchy_schema_version
                    FROM content_meta
                    WHERE hierarchy_schema_version >= ? AND path IN ({marks})
                """, (CURRENT_HIERARCHY_SCHEMA_VERSION, *candidates)).fetchall()
            else:
                c_set = set(candidates)
                all_meta = self.db.execute("""
                    SELECT path, name, extension, mtime, ctime, reference_date, hierarchy_schema_version
                    FROM content_meta
                    WHERE hierarchy_schema_version >= ?
                """, (CURRENT_HIERARCHY_SCHEMA_VERSION,)).fetchall()
                meta_rows = [r for r in all_meta if r["path"] in c_set or os.path.abspath(r["path"]) in c_set]

        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        valid_meta = {}
        for r in meta_rows:
            raw_p = r["path"]
            p = os.path.abspath(raw_p)
            if excluded_name(r["name"] or os.path.basename(p)):
                continue
            if any(part.casefold() == "$recycle.bin" for part in Path(p).parts):
                continue
            if allowed is not None and not any(
                os.path.commonpath((os.path.normcase(p), root)) == root
                for root in allowed
                if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(p)[0].casefold()
            ):
                continue
            ext = r["extension"] or Path(p).suffix.lower().lstrip(".")
            if parsed["ext"] and ext not in parsed["ext"]:
                continue
            if parsed["path"] and not all(v.casefold() in p.casefold() for v in parsed["path"]):
                continue
            ref_date = r["reference_date"]
            if parsed["after"] and (not ref_date or ref_date < parsed["after"]):
                continue
            if parsed["before"] and (not ref_date or ref_date >= parsed["before"]):
                continue
            valid_meta[raw_p] = r
            valid_meta[p] = r

        if not valid_meta:
            return []

        # 3. 일치 문단 및 BM25 점수 조회 (FTS MATCH로 검색어 포함 문단만 추출)
        para_rows = []
        with self._lock:
            if fts_terms:
                match_expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in fts_terms)
                try:
                    para_rows = self.db.execute("""
                        SELECT path, name, paragraph_index, level, level_rank, body, bm25(content_paragraph_fts) AS bm25_rank
                        FROM content_paragraph_fts
                        WHERE content_paragraph_fts MATCH ?
                    """, (match_expr,)).fetchall()
                except sqlite3.OperationalError:
                    para_rows = self.db.execute("""
                        SELECT path, name, paragraph_index, level, level_rank, body, 0.0 AS bm25_rank
                        FROM content_paragraph_fts
                        WHERE content_paragraph_fts MATCH ?
                    """, (match_expr,)).fetchall()
            else:
                term_conds = " OR ".join("body LIKE ?" for _ in terms)
                params = ["%" + t + "%" for t in terms]
                para_rows = self.db.execute(f"""
                    SELECT path, name, paragraph_index, level, level_rank, body, 0.0 AS bm25_rank
                    FROM content_paragraph_fts
                    WHERE {term_conds}
                """, params).fetchall()

        # 4. 문서별 문단 그룹화 및 일치 여부 / 점수 집계
        from collections import defaultdict
        paras_by_path = defaultdict(list)
        for pr in para_rows:
            pr_path = pr["path"]
            matched_key = pr_path if pr_path in valid_meta else os.path.abspath(pr_path)
            if matched_key in valid_meta:
                paras_by_path[matched_key].append(pr)

        # 제외어 포함 문서 사전 추출
        excluded_paths = set()
        if parsed["exclude"]:
            with self._lock:
                for ex in parsed["exclude"]:
                    if len(ex) >= 3:
                        ex_expr = '"' + ex.replace('"', '""') + '"'
                        try:
                            for er in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE content_paragraph_fts MATCH ?", (ex_expr,)):
                                excluded_paths.add(er[0])
                                excluded_paths.add(os.path.abspath(er[0]))
                        except sqlite3.OperationalError:
                            for er in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + ex + "%",)):
                                excluded_paths.add(er[0])
                                excluded_paths.add(os.path.abspath(er[0]))
                    else:
                        for er in self.db.execute("SELECT DISTINCT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + ex + "%",)):
                            excluded_paths.add(er[0])
                            excluded_paths.add(os.path.abspath(er[0]))

        prepared = []
        count_terms = [(t, t) for t in parsed["terms"]] + [(p, p) for p in parsed["phrases"]]

        for path, p_list in paras_by_path.items():
            if path in excluded_paths or os.path.abspath(path) in excluded_paths:
                continue
            meta = valid_meta.get(path)
            if not meta:
                continue

            combined_matched_text = "\n".join(p["body"] or "" for p in p_list)
            combined_folded = combined_matched_text.casefold()

            # 전체 문서 AND 검사
            if any(t.casefold() not in combined_folded for t in terms):
                continue

            # N 근접도 검사
            if parsed["near"] is not None and len(terms) > 1:
                word_spans = [(m.group().casefold(), m.start(), m.end()) for m in re.finditer(r"\S+", combined_matched_text)]
                term_positions = [[i for i, (word, _, _) in enumerate(word_spans) if term.casefold() in word]
                                  for term in terms]
                if any(not pos for pos in term_positions):
                    continue
                if not any(max(combo) - min(combo) <= parsed["near"] + 1
                           for combo in __import__('itertools').product(*term_positions)):
                    continue

            # 언급 횟수 집계
            match_counts = {label: combined_folded.count(term.casefold()) for label, term in count_terms}
            total_matches = sum(match_counts.values())

            # 일치 문단 수집
            matching_paras = []
            for p in p_list:
                p_body = p["body"] or ""
                p_folded = p_body.casefold()
                if any(t.casefold() in p_folded for t in terms):
                    p_idx = int(p["paragraph_index"])
                    p_rank = int(p["level_rank"]) if p["level_rank"] is not None else LEVEL_ORDER.index("body")
                    p_bm25 = float(p["bm25_rank"]) if "bm25_rank" in p.keys() and p["bm25_rank"] is not None else 0.0
                    matching_paras.append(
                        ParagraphMatch(
                            paragraph_index=p_idx,
                            level=p["level"],
                            level_rank=p_rank,
                            match_counts={label: p_folded.count(term.casefold()) for label, term in count_terms},
                            bm25=p_bm25,
                            snippet="",
                            highlights=[],
                        )
                    )

            if not matching_paras:
                best_level = LEVEL_LABELS["body"]
                best_level_rank = LEVEL_ORDER.index("body")
                best_bm25 = 0.0
                target_para_body = p_list[0]["body"] if p_list else ""
            else:
                best_level, best_level_rank = _best_level(matching_paras)
                best_bm25 = min(m.bm25 for m in matching_paras)
                highest_matches = [m for m in matching_paras if m.level_rank == best_level_rank]
                chosen_match = highest_matches[0]
                target_para_body = next((p["body"] for p in p_list if int(p["paragraph_index"]) == chosen_match.paragraph_index), p_list[0]["body"])

            doc_date = _document_date(meta["ctime"], meta["mtime"])
            file_name = meta["name"] or os.path.basename(path)

            prepared.append({
                "path": path,
                "name": file_name,
                "_target_body": target_para_body or "",
                "score": total_matches,
                "match_counts": match_counts,
                "total_matches": total_matches,
                "position": {"page": None, "sheet": None, "row": None},
                "best_level": best_level,
                "_best_level_rank": best_level_rank,
                "_document_date": doc_date,
                "_bm25_score": best_bm25,
            })

        # 5. 정렬 및 순위 부여
        _sort_hierarchy_results(prepared, sort=sort)
        final_items = prepared[:lim]
        for idx, item in enumerate(final_items):
            # 스니펫·하이라이트는 화면에 보일 상위 결과에만 만든다(N214B 속도 개선, 결과 동일)
            target_para_body = item.pop("_target_body")
            t_folded = target_para_body.casefold()
            offsets = [t_folded.find(t.casefold()) for t in terms if t_folded.find(t.casefold()) >= 0]
            first = min(offsets) if offsets else 0
            start, end = max(0, first - 70), min(len(target_para_body), first + 180)
            snippet = target_para_body[start:end]
            spans = []
            for term in terms:
                match = re.search(re.escape(term), snippet, re.I)
                if match:
                    spans.append([match.start(), match.end()])
            ordered = {}
            for key, value in item.items():
                ordered[key] = value
                if key == "name":
                    ordered["snippet"] = snippet
                    ordered["highlights"] = spans
            item.clear()
            item.update(ordered)
            item["relevance_rank"] = idx + 1
            item.pop("_best_level_rank", None)
            item.pop("_document_date", None)
            item.pop("_bm25_score", None)
        return final_items

    @staticmethod
    def _keyword_match_expression(parsed):
        """Build FTS5 AND query while retaining phrases and excluding operators."""
        positive = [*parsed["terms"], *parsed["phrases"]]
        if not positive:
            raise ValueError("본문 검색어를 입력해 주세요.")
        def quote(term):
            return '"' + term.replace('"', '""') + '"'
        expression = " AND ".join(quote(term) for term in positive if len(term) >= 3)
        if not expression:
            return None
        if parsed["near"] is not None and len(positive) > 1:
            expression = " AND ".join(quote(term) for term in positive if len(term) >= 3)
        return expression

    def keyword_search(self, query, *, roots=None, limit=100, offset=0):
        """Docufinder식 키워드 검색. 위계 필드 없이 BM25로 문서 순위를 정한다."""
        parsed = self.parse_query(query)
        positive = [*parsed["terms"], *parsed["phrases"]]
        if not positive:
            raise ValueError("본문 검색어를 입력해 주세요.")
        if type(limit) is not int or not 1 <= limit <= 500 or type(offset) is not int or offset < 0:
            raise ValueError("결과 범위를 확인해 주세요.")
        # 레거시 Office 그룹 확장
        groups = ({"hwp", "hwpx"}, {"doc", "docx"}, {"xls", "xlsx"}, {"ppt", "pptx"})
        extensions = set(parsed["ext"])
        for group in groups:
            if extensions & group:
                extensions.update(group)
        parsed["ext"] = extensions
        fts_positive = [t for t in parsed["terms"] if len(t) >= 3]
        match = " AND ".join('"' + t.replace('"', '""') + '"' for t in fts_positive if t not in parsed["phrases"])
        short_positive = [t for t in positive if len(t) < 3]
        allowed = [os.path.normcase(os.path.abspath(root)) for root in roots] if roots else None
        clauses, params = [], []
        candidate_paths = None
        for term in parsed["terms"]:
            if len(term) >= 3:
                clauses.append("content_paragraph_fts MATCH ?")
                params.append('"' + term.replace('"', '""') + '"')
            else:
                clauses.append("body LIKE ?"); params.append("%" + term + "%")
        for phrase in parsed["phrases"]:
            clauses.append("body LIKE ?"); params.append("%" + phrase + "%")
        where_positive = " AND ".join(clauses)
        with self._lock:
            # Short terms use the gram table only to narrow candidates; LIKE remains the
            # final substring check, preserving the old exact matching behavior.
            if short_positive:
                short_candidates = None
                for term in short_positive:
                    if len(term) == 2:
                        found = {r[0] for r in self.db.execute(
                            "SELECT path FROM content_short_grams WHERE gram=?", (term.casefold(),))}
                    else:
                        found = {r[0] for r in self.db.execute(
                            "SELECT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + term + "%",))}
                    short_candidates = found if short_candidates is None else short_candidates & found
                if short_candidates is not None:
                    candidate_paths = short_candidates
                    if candidate_paths is not None and not candidate_paths:
                        return []
            if short_positive and candidate_paths is not None:
                self.db.execute("CREATE TEMP TABLE IF NOT EXISTS keyword_candidate_paths(path TEXT PRIMARY KEY)")
                self.db.execute("DELETE FROM keyword_candidate_paths")
                self.db.executemany("INSERT INTO keyword_candidate_paths(path) VALUES(?)",
                                    ((path,) for path in candidate_paths))
                long_predicates = []
                long_params = []
                for term in parsed["terms"]:
                    if len(term) >= 3:
                        long_predicates.append("p.body LIKE ?")
                        long_params.append("%" + term + "%")
                for phrase in parsed["phrases"]:
                    long_predicates.append("p.body LIKE ?")
                    long_params.append("%" + phrase + "%")
                predicate = " AND ".join(long_predicates) if long_predicates else "1"
                scored_rows = self.db.execute(f"""
                    SELECT p.path,p.name,p.level_rank,p.body,0.0 AS rank
                    FROM keyword_candidate_paths c
                    JOIN content_paragraph_fts p ON p.path=c.path
                    WHERE {predicate}
                """, long_params).fetchall()
            else:
                scored_rows = self.db.execute(f"""
                    SELECT path, name, level_rank, body,
                           bm25(content_paragraph_fts, 0.0, 3.0, 2.0, 1.0, 0.0, 0.0, 1.0) AS rank
                    FROM content_paragraph_fts WHERE {where_positive}
                    ORDER BY rank ASC
                """, params).fetchall()
            if candidate_paths is not None:
                scored_rows = [r for r in scored_rows if r["path"] in candidate_paths]
        # FTS5 bm25 weights: filename=3, body=1. Add a hierarchy boost to the
        # paragraph score for levels 0..3, then proximity/phrase boosts per document.
        doc_scores = {}
        for scored in scored_rows:
            path = scored["path"]
            rank = float(scored["rank"])
            name_folded = (scored["name"] or "").casefold()
            # Filename is UNINDEXED in this legacy FTS5 schema, so apply the exact
            # requested 3:1 field weight as an explicit weighted occurrence count.
            body_term_count = sum((scored["body"] or "").casefold().count(term.casefold()) for term in positive)
            filename_term_count = sum(term.casefold() in name_folded for term in positive)
            rank -= 0.001 * (body_term_count + 3.0 * filename_term_count)
            level_rank = int(scored["level_rank"] if scored["level_rank"] is not None else LEVEL_ORDER.index("body"))
            if level_rank <= 3:
                rank -= 0.002 * (4 - level_rank)
            prior = doc_scores.get(path)
            doc_scores[path] = min(rank, prior) if prior is not None else rank
        if short_positive and candidate_paths is not None:
            for candidate_path in candidate_paths:
                doc_scores.setdefault(candidate_path, 0.0)
        rows = [{"path": path, "best_bm25": score} for path, score in doc_scores.items()]
        if short_positive and candidate_paths is not None:
            rows = [row for row in rows if row["path"] in candidate_paths]
        rows = rows[:100000]
        excluded = set()
        excluded_short = []
        with self._lock:
            for term in parsed["exclude"]:
                if len(term) < 3:
                    excluded_short.append(term)
                if len(term) >= 3:
                    expr = '"' + term.replace('"', '""') + '"'
                    try:
                        excluded.update(row[0] for row in self.db.execute(
                            "SELECT DISTINCT path FROM content_paragraph_fts WHERE content_paragraph_fts MATCH ?", (expr,)))
                    except sqlite3.OperationalError:
                        pass
                excluded.update(row[0] for row in self.db.execute(
                    "SELECT DISTINCT path FROM content_paragraph_fts WHERE body LIKE ?", ("%" + term + "%",)))
            metas = {row["path"]: row for row in self.db.execute(
                "SELECT path,name,extension,mtime,reference_date FROM content_meta WHERE path IN (" +
                ",".join("?" for _ in rows) + ")", tuple(row["path"] for row in rows))} if rows else {}
        ranked = []
        candidate_path_set = {r["path"] for r in rows}
        candidate_texts = {}
        with self._lock:
            if candidate_path_set:
                marks = ",".join("?" for _ in candidate_path_set)
                if short_positive and candidate_paths is not None:
                    candidate_texts = {r["path"]: r["body"] or "" for r in self.db.execute(
                        f"SELECT path, body FROM content_paragraph_fts WHERE path IN ({marks})",
                        tuple(candidate_path_set))}
                else:
                    candidate_texts = {r["path"]: r["body"] or "" for r in self.db.execute(
                        f"SELECT path, group_concat(body, char(10)) AS body FROM content_paragraph_fts WHERE path IN ({marks}) GROUP BY path",
                        tuple(candidate_path_set))}
        rows = [row for row in rows if all(term.casefold() in candidate_texts.get(row["path"], "").casefold()
                                           for term in parsed["terms"]) and all(
                phrase.casefold() in candidate_texts.get(row["path"], "").replace('"', '').casefold()
                for phrase in parsed["phrases"]) and not any(
                term.casefold() in candidate_texts.get(row["path"], "").casefold()
                for term in [*parsed["exclude"], *excluded_short])]
        paragraph_rows_by_path = {}
        candidate_path_set = {row["path"] for row in rows}
        with self._lock:
            if candidate_path_set:
                marks = ",".join("?" for _ in candidate_path_set)
                for paragraph_row in self.db.execute(
                    f"SELECT path,paragraph_index,body,level_rank FROM content_paragraph_fts WHERE path IN ({marks})",
                    tuple(candidate_path_set)):
                    paragraph_rows_by_path.setdefault(paragraph_row["path"], []).append(paragraph_row)
        # 근접 검색은 동일 문단 내 양성 용어 사이의 단어 간격으로 제한한다.
        if parsed["near"] is not None and len(positive) > 1:
            near = parsed["near"]
            filtered = []
            for row in rows:
                paragraphs_for_near = paragraph_rows_by_path.get(row["path"], [])
                proximity_terms = [*parsed["terms"]]
                if len(proximity_terms) < 2:
                    proximity_terms = positive
                if any(_terms_are_near(paragraph["body"] or "", proximity_terms, near) for paragraph in paragraphs_for_near):
                    filtered.append(row)
            rows = filtered
        for row in rows:
            path = row["path"]
            para_candidates = paragraph_rows_by_path.get(path, [])
            valid_para_indices = {int(p["paragraph_index"]) for p in para_candidates
                if all(term.casefold() in (p["body"] or "").casefold() for term in parsed["terms"])
                and all(phrase.casefold() in (p["body"] or "").casefold() for phrase in parsed["phrases"])}
            if not valid_para_indices:
                continue
            meta = metas.get(path)
            if not meta or path in excluded or os.path.abspath(path) in excluded:
                continue
            normalized = os.path.normcase(os.path.abspath(path))
            if any(part.casefold() == "$recycle.bin" for part in Path(path).parts):
                continue
            if allowed is not None and not any(os.path.commonpath((normalized, root)) == root for root in allowed
                    if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(normalized)[0].casefold()):
                continue
            ext = (meta["extension"] or Path(path).suffix.lstrip(".")).lower()
            if parsed["ext"] and ext not in parsed["ext"]:
                continue
            if parsed["path"] and not all(value.casefold() in path.casefold() for value in parsed["path"]):
                continue
            ref_date = meta["reference_date"] or ""
            if ref_date and len(ref_date) == 4:
                ref_date += "-01-01"
            elif ref_date and len(ref_date) == 7:
                ref_date += "-01"
            if not ref_date and meta["mtime"]:
                ref_date = date.fromtimestamp(meta["mtime"]).isoformat()
            text_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", candidate_texts.get(path, ""))
            if text_date:
                ref_date = text_date.group(1)
            after = parsed["after"]
            before = parsed["before"]
            if after and len(after) == 4: after += "-01-01"
            elif after and len(after) == 7: after += "-01"
            if before and len(before) == 4: before += "-12-31"
            elif before and len(before) == 7: before += "-31"
            if after and (not ref_date or ref_date < after):
                continue
            if before and (not ref_date or ref_date > before):
                continue
            # Proximity bonus: reward the closest pair of positive terms in a single
            # paragraph. Explicit quoted phrases also get a phrase-match bonus.
            proximity_bonus = 0.0
            phrase_bonus = 0.0
            if parsed["near"] is None or len(positive) > 1 or parsed["phrases"]:
                proximity_paragraphs = para_candidates
            else:
                proximity_paragraphs = ()
            for paragraph in proximity_paragraphs:
                text = paragraph["body"] or ""
                if all(term.casefold() in text.casefold() for term in positive):
                    terms_for_distance = parsed["terms"] or positive
                    words = [m.group().casefold() for m in re.finditer(r"\S+", text)]
                    positions = [[i for i, word in enumerate(words) if term.casefold() in word]
                                 for term in terms_for_distance]
                    if positions and all(positions):
                        import itertools
                        distance = min(max(combo) - min(combo) for combo in itertools.product(*positions))
                        proximity_bonus = max(proximity_bonus, 0.20 / (1 + distance))
                    if parsed["phrases"] and all(p.casefold() in text.casefold() for p in parsed["phrases"]):
                        phrase_bonus = max(phrase_bonus, 0.35)
            filename_bonus = 0.0
            ranked.append((float(row["best_bm25"]) - proximity_bonus - phrase_bonus - filename_bonus, path, meta))
        ranked.sort(key=lambda value: (value[0], value[1].casefold()))
        selected = ranked[offset:offset + limit]
        results = []
        for score, path, meta in selected:
            conditions, match_params = [], []
            if match and not parsed["phrases"]:
                conditions.append("content_paragraph_fts MATCH ?"); match_params.append(match)
            else:
                for term in parsed["terms"]:
                    if len(term) >= 3:
                        conditions.append("content_paragraph_fts MATCH ?")
                        match_params.append('"' + term.replace('"', '""') + '"')
                    else:
                        conditions.append("body LIKE ?"); match_params.append("%" + term + "%")
                for phrase in parsed["phrases"]:
                    conditions.append("body LIKE ?"); match_params.append("%" + phrase.replace('"', '""') + "%")
            for term in short_positive:
                conditions.append("body LIKE ?"); match_params.append("%" + term + "%")
            match_where = " AND ".join(conditions)
            with self._lock:
                if short_positive:
                    paragraphs = self.db.execute(f"""
                        SELECT paragraph_index, body, location_label, section, 0.0 AS rank
                        FROM content_paragraph_fts WHERE path=? AND {match_where}
                        ORDER BY CAST(paragraph_index AS INTEGER) ASC LIMIT 3
                    """, [path, *match_params]).fetchall()
                else:
                    paragraphs = self.db.execute(f"""
                        SELECT paragraph_index, body, location_label, section,
                               bm25(content_paragraph_fts, 0.0, 3.0, 2.0, 1.0, 0.0, 0.0, 1.0) AS rank
                        FROM content_paragraph_fts WHERE path=? AND {match_where}
                        ORDER BY rank ASC, CAST(paragraph_index AS INTEGER) ASC LIMIT 3
                    """, [path, *match_params]).fetchall()
            paragraphs = [p for p in paragraphs if int(p["paragraph_index"]) in valid_para_indices]
            locations = []
            for paragraph in paragraphs:
                text = paragraph["body"] or ""
                folded = text.casefold()
                starts = [folded.find(term.casefold()) for term in positive if folded.find(term.casefold()) >= 0]
                if not starts:
                    continue
                first = min(starts); start = max(0, first - 70); end = min(len(text), first + 180)
                snippet = text[start:end]
                highlights = [[m.start(), m.end()] for term in positive
                              for m in list(re.finditer(re.escape(term), snippet, re.I))]
                label = paragraph["location_label"] or f"문단 {int(paragraph['paragraph_index']) + 1}"
                location = {"page": None, "sheet": None, "row": None, "label": label}
                page_match = re.search(r"(\d+)쪽", label)
                row_match = re.search(r"(.+?)\s+(\d+)행", label)
                line_match = re.fullmatch(r"(\d+)행", label)
                if page_match:
                    location["page"] = int(page_match.group(1))
                if row_match:
                    location["sheet"], location["row"] = row_match.group(1), int(row_match.group(2))
                elif line_match:
                    location["row"] = int(line_match.group(1))
                locations.append({"paragraph_index": int(paragraph["paragraph_index"]), "snippet": snippet,
                                  "highlights": highlights, "position": location})
            results.append({"path": path, "name": meta["name"] or os.path.basename(path),
                            "extension": meta["extension"] or Path(path).suffix.lstrip("."),
                            "mtime": meta["mtime"], "folder_path": os.path.dirname(path),
                            "folder_name": os.path.basename(os.path.dirname(path)),
                            "locations": locations, "snippet": locations[0]["snippet"] if locations else "",
                            "highlights": locations[0]["highlights"] if locations else [],
                            "position": locations[0]["position"] if locations else {"page": None, "sheet": None, "row": None},
                            "score": score, "relevance_rank": offset + len(results) + 1})
        return results

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
        path_str = os.fspath(path)
        path_abs = os.path.abspath(path_str)
        path_variants = list(dict.fromkeys([
            path_str,
            path_abs,
            os.path.normpath(path_str),
            os.path.normpath(path_abs),
            path_str.replace("\\", "/"),
            path_str.replace("/", "\\"),
            path_abs.replace("\\", "/"),
            path_abs.replace("/", "\\"),
        ]))
        placeholders = ",".join("?" for _ in path_variants)

        with self._lock:
            selected = None
            # 1. content_paragraph_fts에서 문단 결합 본문 조회
            try:
                para_row = self.db.execute(f"""
                    SELECT GROUP_CONCAT(body, CHAR(10)) AS body,
                           (SELECT reference_date FROM content_meta WHERE path IN ({placeholders}) LIMIT 1) AS reference_date,
                           path
                    FROM (SELECT path, body FROM content_paragraph_fts WHERE path IN ({placeholders}) ORDER BY paragraph_index ASC)
                    GROUP BY path
                    LIMIT 1
                """, (*path_variants, *path_variants)).fetchone()
                if para_row and para_row["body"]:
                    selected = para_row
            except sqlite3.OperationalError:
                pass

            # 2. 없으면 content_fts (구형 단일 본문 색인) 조회
            if not selected:
                try:
                    selected = self.db.execute(f"""
                        SELECT f.body,
                               COALESCE(m.reference_date, (SELECT reference_date FROM content_meta WHERE path IN ({placeholders}) LIMIT 1)) AS reference_date,
                               f.path
                        FROM content_fts f
                        LEFT JOIN content_meta m ON m.path=f.path
                        WHERE f.path IN ({placeholders})
                        LIMIT 1
                    """, (*path_variants, *path_variants)).fetchone()
                except sqlite3.OperationalError:
                    pass

            if not selected:
                return None, []

            matched_path = selected["path"] if ("path" in selected.keys() and selected["path"]) else path_str
            exclude_paths = set(path_variants)
            exclude_paths.add(matched_path)
            exclude_paths.add(os.path.abspath(matched_path))

            seen_paths = set(exclude_paths)
            rows = []

            # (1) content_paragraph_fts에서 후보 수집
            try:
                ex_list = list(seen_paths)
                ex_placeholders = ",".join("?" for _ in ex_list)
                p_rows = self.db.execute(f"""
                    SELECT p.path, p.name, GROUP_CONCAT(p.body, CHAR(10)) AS body, m.reference_date
                    FROM (SELECT path, name, body FROM content_paragraph_fts WHERE path NOT IN ({ex_placeholders}) ORDER BY paragraph_index ASC) p
                    LEFT JOIN content_meta m ON m.path=p.path
                    GROUP BY p.path
                """, ex_list).fetchall()
                for r in p_rows:
                    rows.append(r)
                    seen_paths.add(r["path"])
                    seen_paths.add(os.path.abspath(r["path"]))
            except sqlite3.OperationalError:
                pass

            # (2) content_fts에서 아직 수집되지 않은 구형 문서 후보 수집
            try:
                ex_list = list(seen_paths)
                ex_placeholders = ",".join("?" for _ in ex_list)
                legacy_rows = self.db.execute(f"""
                    SELECT f.path, f.name, f.body, m.reference_date
                    FROM content_fts f
                    LEFT JOIN content_meta m ON m.path=f.path
                    WHERE f.path NOT IN ({ex_placeholders})
                """, ex_list).fetchall()
                for r in legacy_rows:
                    rows.append(r)
                    seen_paths.add(r["path"])
                    seen_paths.add(os.path.abspath(r["path"]))
            except sqlite3.OperationalError:
                pass

        allowed = [os.path.normcase(os.path.abspath(r)) for r in roots] if roots else None
        candidates = []
        for row in rows:
            row_path = row["path"]
            if allowed is not None:
                item_path = os.path.normcase(os.path.abspath(row_path))
                if not any(
                    os.path.commonpath((item_path, root)) == root
                    for root in allowed
                    if os.path.splitdrive(root)[0].casefold() == os.path.splitdrive(os.path.abspath(row_path))[0].casefold()
                ):
                    continue
            candidates.append(dict(row))
        return dict(selected) if selected else None, candidates
