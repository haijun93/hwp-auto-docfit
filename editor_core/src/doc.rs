//! 문서: 버퍼 + 여러 단계 실행취소/다시실행(입력 묶음) + 줄바꿈/인코딩 + 저장.

use crate::buffer::TextBuffer;
use crate::fileio::{self, Encoding, LineEnding};
use crate::search::{self, SearchOpts};
use std::collections::VecDeque;
use std::path::Path;

pub type Res<T> = Result<T, String>;

#[derive(Clone, Debug)]
struct Edit {
    pos: usize,
    removed: String,
    inserted: String,
    /// Backspace 연속 삭제에서 앞쪽에 붙일 조각(나중에 지운 것이 뒤). 매 글자 앞붙임 복사를 피하려고
    /// 모아 두었다가 실행취소·다시실행 직전에 `removed` 앞에 한 번에 합친다.
    front: Vec<String>,
}

impl Edit {
    fn new(pos: usize, removed: String, inserted: String) -> Self {
        Edit { pos, removed, inserted, front: Vec::new() }
    }
    fn flatten(&mut self) {
        if self.front.is_empty() {
            return;
        }
        let extra: usize = self.front.iter().map(String::len).sum();
        let mut s = String::with_capacity(extra + self.removed.len());
        for piece in self.front.iter().rev() {
            s.push_str(piece);
        }
        s.push_str(&self.removed);
        self.removed = s;
        self.front.clear();
    }
}

struct Group {
    edits: Vec<Edit>,
    /// 다음 입력이 이어 붙을 수 있는 묶음(자동 묶기용).
    open: bool,
    /// begin_group~end_group으로 만든 묶음은 자동 병합하지 않는다.
    explicit: bool,
}

const MAX_UNDO_GROUPS: usize = 5000;

pub struct Document {
    pub(crate) buf: TextBuffer,
    undo: VecDeque<Group>,
    redo: Vec<Group>,
    depth: u32,
    clean_marker: Option<usize>,
    pub line_ending: LineEnding,
    pub mixed_line_endings: bool,
    pub encoding: Encoding,
    pub path: Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Stats {
    pub lines: usize,
    pub chars: usize,
    pub bytes: usize,
    pub words: usize,
}

/// 상태 표시줄 값(`Document::status`).
#[derive(Debug, Clone, PartialEq)]
pub struct Status {
    pub line: usize,
    pub col: usize,
    pub lines: usize,
    /// 줄바꿈을 한 글자로 센 전체 글자(유니코드 스칼라) 수.
    pub chars: usize,
    pub chars_no_newline: usize,
    pub selected_chars: Option<usize>,
    /// 내부(LF) 기준 UTF-8 바이트 수.
    pub bytes: usize,
    pub line_ending: LineEnding,
    pub mixed_line_endings: bool,
    pub encoding: Encoding,
}

/// 모두 바꾸기 결과: 바꾼 개수와 바뀐 글 구간(새 위치 기준, 바뀐 것이 없으면 `None`).
#[derive(Debug, Clone, PartialEq)]
pub struct Replaced {
    pub count: usize,
    pub range: Option<(usize, usize)>,
}

impl Default for Document {
    fn default() -> Self {
        Self::new()
    }
}

impl Document {
    pub fn new() -> Self {
        Document {
            buf: TextBuffer::new(),
            undo: VecDeque::new(),
            redo: Vec::new(),
            depth: 0,
            clean_marker: Some(0),
            line_ending: LineEnding::Crlf, // 새 문서는 Windows 메모장처럼 CRLF
            mixed_line_endings: false,
            encoding: Encoding::Utf8,
            path: None,
        }
    }

    /// 문자열에서 문서를 만든다. 줄바꿈 형식을 감지하고 내부는 LF로 통일한다.
    pub fn from_text(text: &str) -> Self {
        let mut d = Document::new();
        let text = text.strip_prefix('\u{feff}').unwrap_or(text);
        let (le, mixed) = fileio::detect_line_ending(text);
        d.line_ending = if text.contains(['\r', '\n']) { le } else { LineEnding::Crlf };
        d.mixed_line_endings = mixed;
        d.buf.insert(0, &fileio::normalize_to_lf(text));
        d
    }

    pub fn from_bytes(bytes: &[u8]) -> Res<Self> {
        let (text, enc) = fileio::decode(bytes)?;
        let mut d = Document::from_text(&text);
        d.encoding = enc;
        Ok(d)
    }

    /// 인코딩을 지정해 연다(자동 감지가 틀렸을 때 다시 열기용).
    pub fn from_bytes_as(bytes: &[u8], enc: Encoding) -> Res<Self> {
        let text = fileio::decode_as(bytes, enc)?;
        let mut d = Document::from_text(&text);
        d.encoding = enc;
        Ok(d)
    }

    /// 파일을 연다. `enc`가 없으면 BOM·UTF-8·CP949 순으로 자동 감지한다.
    pub fn open(path: &Path) -> Res<Self> {
        Self::open_as(path, None)
    }

    pub fn open_as(path: &Path, enc: Option<Encoding>) -> Res<Self> {
        let bytes = std::fs::read(path).map_err(|e| format!("파일을 열 수 없습니다: {e}"))?;
        let mut d = match enc {
            Some(e) => Document::from_bytes_as(&bytes, e)?,
            None => Document::from_bytes(&bytes)?,
        };
        d.path = Some(path.to_string_lossy().into_owned());
        Ok(d)
    }

    // ---- 조회 ----
    pub fn len(&self) -> usize {
        self.buf.len()
    }
    pub fn is_empty(&self) -> bool {
        self.buf.is_empty()
    }
    pub fn text(&mut self) -> &str {
        self.buf.as_str()
    }
    pub fn slice(&self, start: usize, end: usize) -> Res<String> {
        self.check_range(start, end)?;
        Ok(self.buf.slice(start, end))
    }
    pub fn line_count(&self) -> usize {
        self.buf.line_count()
    }
    pub fn line_start(&self, line: usize) -> usize {
        self.buf.line_start(line)
    }
    pub fn line_end(&self, line: usize) -> usize {
        self.buf.line_end(line)
    }
    pub fn line_of(&self, pos: usize) -> usize {
        self.buf.line_of(pos)
    }
    pub fn line_text(&self, line: usize) -> String {
        self.buf.slice(self.buf.line_start(line), self.buf.line_end(line))
    }

    /// 메모장식 (줄, 열): 둘 다 1부터, 열은 글자 단위.
    pub fn line_col(&self, pos: usize) -> Res<(usize, usize)> {
        self.check_pos(pos)?;
        let line = self.buf.line_of(pos);
        Ok((line + 1, self.buf.count_chars(self.buf.line_start(line), pos) + 1))
    }

    /// (줄, 열) → 바이트 오프셋. 범위를 넘으면 줄/문서 끝으로 맞춘다.
    pub fn offset_of(&self, line1: usize, col1: usize) -> usize {
        let line = line1.max(1).min(self.buf.line_count()) - 1;
        let (s, e) = (self.buf.line_start(line), self.buf.line_end(line));
        let mut pos = s;
        let mut left = col1.max(1) - 1;
        while left > 0 && pos < e {
            pos += 1;
            while pos < e && !self.buf.is_char_boundary(pos) {
                pos += 1;
            }
            left -= 1;
        }
        pos
    }

    /// 상태 표시줄 값. `pos`는 커서(바이트), `sel`은 선택 범위(있으면 선택 글자 수 포함).
    /// 줄·열은 1부터, 열은 글자(유니코드 스칼라) 경계 기준이다. 모두 O(줄 길이) 이하라 키 입력마다 불러도 된다.
    pub fn status(&self, pos: usize, sel: Option<(usize, usize)>) -> Res<Status> {
        let (line, col) = self.line_col(pos)?;
        let selected_chars = match sel {
            Some((a, b)) => {
                self.check_range(a, b)?;
                Some(self.buf.count_chars(a, b))
            }
            None => None,
        };
        let chars = self.buf.char_count();
        let lines = self.buf.line_count();
        Ok(Status {
            line,
            col,
            lines,
            chars,
            chars_no_newline: chars - (lines - 1),
            selected_chars,
            bytes: self.buf.len(),
            line_ending: self.line_ending,
            mixed_line_endings: self.mixed_line_endings,
            encoding: self.encoding,
        })
    }

    pub fn stats(&mut self) -> Stats {
        let words = self.buf.as_str().split_whitespace().count();
        Stats { lines: self.buf.line_count(), chars: self.buf.char_count(), bytes: self.buf.len(), words }
    }

    pub fn byte_to_utf16(&mut self, pos: usize) -> Res<usize> {
        self.check_pos(pos)?;
        Ok(self.buf.as_str()[..pos].chars().map(char::len_utf16).sum())
    }
    pub fn utf16_to_byte(&mut self, unit: usize) -> Res<usize> {
        let mut u = 0;
        for (i, c) in self.buf.as_str().char_indices() {
            if u == unit {
                return Ok(i);
            }
            if u > unit {
                return Err("UTF-16 위치가 대리 쌍 한가운데입니다.".into());
            }
            u += c.len_utf16();
        }
        if u == unit { Ok(self.buf.len()) } else { Err("UTF-16 위치가 범위를 벗어났습니다.".into()) }
    }

    fn check_pos(&self, pos: usize) -> Res<()> {
        if pos > self.buf.len() {
            return Err(format!("위치 {pos}가 문서 길이 {}를 넘었습니다.", self.buf.len()));
        }
        if !self.buf.is_char_boundary(pos) {
            return Err(format!("위치 {pos}는 글자 경계가 아닙니다."));
        }
        Ok(())
    }
    fn check_range(&self, s: usize, e: usize) -> Res<()> {
        if s > e {
            return Err("시작이 끝보다 큽니다.".into());
        }
        self.check_pos(s)?;
        self.check_pos(e)
    }

    // ---- 편집 ----
    pub fn insert(&mut self, pos: usize, text: &str) -> Res<usize> {
        self.replace_range(pos, pos, text)
    }
    pub fn delete(&mut self, start: usize, end: usize) -> Res<usize> {
        self.replace_range(start, end, "")
    }

    /// `[start,end)`를 `text`로 바꾼다. 바꾼 뒤 커서 위치(삽입 끝)를 돌려준다.
    /// 외부 입력의 `\r\n`·`\r`는 `\n`으로 통일된다.
    pub fn replace_range(&mut self, start: usize, end: usize, text: &str) -> Res<usize> {
        self.check_range(start, end)?;
        let owned;
        let text = if text.contains('\r') {
            owned = fileio::normalize_to_lf(text);
            owned.as_str()
        } else {
            text
        };
        if start == end && text.is_empty() {
            return Ok(start);
        }
        let removed = self.buf.delete(start, end);
        self.buf.insert(start, text);
        self.record(Edit::new(start, removed, text.to_string()));
        Ok(start + text.len())
    }

    fn record(&mut self, e: Edit) {
        if !self.redo.is_empty() {
            self.redo.clear();
        }
        if let Some(m) = self.clean_marker {
            if m > self.undo.len() {
                self.clean_marker = None;
            }
        }
        if self.depth > 0 {
            if let Some(g) = self.undo.back_mut() {
                g.edits.push(e);
            }
            return;
        }
        if self.try_merge(&e) {
            return;
        }
        if let Some(g) = self.undo.back_mut() {
            g.open = false;
        }
        self.undo.push_back(Group { edits: vec![e], open: true, explicit: false });
        if self.undo.len() > MAX_UNDO_GROUPS {
            self.undo.pop_front();
            self.clean_marker = match self.clean_marker {
                Some(m) if m > 0 => Some(m - 1),
                _ => None,
            };
        }
    }

    /// 직전 묶음이 열려 있고 이번 편집이 "이어 쓰기/이어 지우기/조합 갱신"이면 합친다.
    fn try_merge(&mut self, e: &Edit) -> bool {
        let marker_at_end = self.clean_marker == Some(self.undo.len());
        let Some(g) = self.undo.back_mut() else { return false };
        if !g.open || g.explicit || g.edits.len() != 1 {
            return false;
        }
        let p = &mut g.edits[0];
        let p_end = p.pos + p.inserted.len();
        let e_rm_end = e.pos + e.removed.len();
        // (A) 방금 넣은 글 안(끝 포함)에서 바꾸기 — 이어 쓰기, 한글 조합 갱신, 방금 쓴 글 지우기
        if e.pos >= p.pos && e_rm_end <= p_end && !p.inserted.is_empty() {
            let breaks = e.inserted.contains('\n')
                || (e.removed.is_empty()
                    && e.inserted.chars().next().is_some_and(char::is_whitespace)
                    && p.inserted.chars().next_back().is_some_and(|c| !c.is_whitespace()));
            if !breaks {
                let a = e.pos - p.pos;
                let b = a + e.removed.len();
                if e.removed.is_empty() && a == p.inserted.len() {
                    p.inserted.push_str(&e.inserted); // 이어 쓰기: 끝에 덧붙이기(복사 없음)
                } else {
                    p.inserted.replace_range(a..b, &e.inserted);
                }
                if marker_at_end {
                    self.clean_marker = None;
                }
                return true;
            }
            return false;
        }
        // (B) 순수 삭제의 연속: Backspace(앞으로) / Delete(제자리)
        if p.inserted.is_empty() && e.inserted.is_empty() && !e.removed.is_empty() {
            if e_rm_end == p.pos {
                p.pos = e.pos;
                p.front.push(e.removed.clone());
            } else if e.pos == p.pos {
                p.removed.push_str(&e.removed);
            } else {
                return false;
            }
            if marker_at_end {
                self.clean_marker = None;
            }
            return true;
        }
        false
    }

    /// 지금까지의 입력을 한 묶음으로 마감한다(커서 이동·붙여넣기 등 경계에서 호출).
    pub fn commit(&mut self) {
        if let Some(g) = self.undo.back_mut() {
            g.open = false;
        }
    }

    /// 여러 편집을 한 번의 실행취소로 묶는다. `end_group`과 짝을 이룬다(중첩 가능).
    pub fn begin_group(&mut self) {
        if self.depth == 0 {
            if let Some(g) = self.undo.back_mut() {
                g.open = false;
            }
            if !self.redo.is_empty() {
                self.redo.clear();
            }
            if self.clean_marker.is_some_and(|m| m > self.undo.len()) {
                self.clean_marker = None;
            }
            self.undo.push_back(Group { edits: Vec::new(), open: true, explicit: true });
        }
        self.depth += 1;
    }

    pub fn end_group(&mut self) {
        if self.depth == 0 {
            return;
        }
        self.depth -= 1;
        if self.depth == 0 {
            if self.undo.back().is_some_and(|g| g.edits.is_empty()) {
                self.undo.pop_back();
            } else if let Some(g) = self.undo.back_mut() {
                g.open = false;
            }
        }
    }

    pub fn can_undo(&self) -> bool {
        !self.undo.is_empty()
    }
    pub fn can_redo(&self) -> bool {
        !self.redo.is_empty()
    }

    fn apply_inverse(&mut self, e: &Edit) {
        self.buf.delete(e.pos, e.pos + e.inserted.len());
        self.buf.insert(e.pos, &e.removed);
    }
    fn apply_forward(&mut self, e: &Edit) {
        self.buf.delete(e.pos, e.pos + e.removed.len());
        self.buf.insert(e.pos, &e.inserted);
    }

    /// 실행취소. 되돌린 뒤 커서 위치를 돌려준다.
    pub fn undo(&mut self) -> Option<usize> {
        if self.depth > 0 {
            self.end_group();
        }
        let mut g = self.undo.pop_back()?;
        g.open = false;
        let mut cursor = 0;
        for e in g.edits.iter_mut().rev() {
            e.flatten();
            self.apply_inverse(e);
            cursor = e.pos + e.removed.len();
        }
        self.redo.push(g);
        Some(cursor)
    }

    pub fn redo(&mut self) -> Option<usize> {
        let mut g = self.redo.pop()?;
        let mut cursor = 0;
        for e in g.edits.iter_mut() {
            e.flatten();
            self.apply_forward(e);
            cursor = e.pos + e.inserted.len();
        }
        self.undo.push_back(g);
        Some(cursor)
    }

    // ---- 찾기·바꾸기 ----
    // 내부 글은 LF뿐이므로 찾는 말·바꿀 말의 CRLF·CR도 LF로 맞춘다(화면 입력 칸에서 온 줄바꿈이 일치하도록).
    pub fn find_next(&mut self, query: &str, from: usize, o: SearchOpts, wrap: bool) -> Option<(usize, usize)> {
        let q = fileio::normalize_to_lf(query);
        let text = self.buf.as_str();
        search::find_next(text, &q, from, o).or_else(|| if wrap && from > 0 { search::find_next(text, &q, 0, o) } else { None })
    }

    pub fn find_all(&mut self, query: &str, o: SearchOpts, limit: usize) -> Vec<(usize, usize)> {
        let q = fileio::normalize_to_lf(query);
        search::find_all(self.buf.as_str(), &q, o, limit)
    }

    /// `[start,end)` 안에 완전히 들어가는 일치만(온전한 낱말 판정은 범위 밖 글자도 본다).
    pub fn find_all_in(&mut self, query: &str, o: SearchOpts, start: usize, end: usize, limit: usize) -> Res<Vec<(usize, usize)>> {
        self.check_range(start, end)?;
        let q = fileio::normalize_to_lf(query);
        Ok(search::find_all_in(self.buf.as_str(), &q, o, start, end, limit))
    }

    /// `from` 이후 첫 일치 하나를 바꾼다. 바꾼 구간과 커서를 돌려준다.
    pub fn replace_next(&mut self, query: &str, with: &str, from: usize, o: SearchOpts, wrap: bool) -> Res<Option<(usize, usize)>> {
        let Some((s, e)) = self.find_next(query, from, o, wrap) else { return Ok(None) };
        let end = self.replace_range(s, e, with)?;
        self.commit();
        Ok(Some((s, end)))
    }

    /// 모두 바꾸기: 한 번의 실행취소. 바꾼 개수를 돌려준다.
    pub fn replace_all(&mut self, query: &str, with: &str, o: SearchOpts) -> Res<usize> {
        Ok(self.replace_all_in(query, with, o, None)?.count)
    }

    /// 범위(`None`이면 문서 전체) 안의 모두 바꾸기. 일치 80,000건이어도 편집 기록은 하나(처음~끝 구간 교체)라
    /// 실행취소 한 번으로 모두 되돌아가고, 안 바뀐 사이 글도 한 번에 복사된다. 바꿀 말이 찾는 말과 같아
    /// 글이 달라지지 않으면 기록을 만들지 않는다(저장 안 된 표시도 생기지 않음).
    pub fn replace_all_in(&mut self, query: &str, with: &str, o: SearchOpts, scope: Option<(usize, usize)>) -> Res<Replaced> {
        let (a, b) = scope.unwrap_or((0, self.buf.len()));
        let hits = self.find_all_in(query, o, a, b, usize::MAX)?;
        let Some(&(first, _)) = hits.first() else { return Ok(Replaced { count: 0, range: None }) };
        let last = hits[hits.len() - 1].1;
        let with = fileio::normalize_to_lf(with);
        let mut rep = String::with_capacity(last - first);
        let mut at = first;
        let text = self.buf.as_str();
        for &(s, e) in &hits {
            rep.push_str(&text[at..s]);
            rep.push_str(&with);
            at = e;
        }
        let count = hits.len();
        if rep == text[first..last] {
            return Ok(Replaced { count, range: Some((first, last)) });
        }
        let new_end = first + rep.len();
        self.begin_group();
        let r = self.replace_range(first, last, &rep);
        self.end_group();
        r?;
        Ok(Replaced { count, range: Some((first, new_end)) })
    }

    // ---- 저장 ----
    pub fn is_dirty(&self) -> bool {
        self.clean_marker != Some(self.undo.len())
    }
    pub fn mark_clean(&mut self) {
        self.clean_marker = Some(self.undo.len());
        self.commit();
    }

    /// 저장할 바이트(줄바꿈·인코딩 적용). CP949로 표현할 수 없는 글자가 있으면 오류.
    pub fn to_bytes(&mut self) -> Res<Vec<u8>> {
        let le = self.line_ending;
        let enc = self.encoding;
        let s = fileio::lf_to(self.buf.as_str(), le);
        fileio::encode(&s, enc)
    }

    /// 저장 인코딩을 바꾼다. 그 인코딩으로 표현할 수 없는 글자가 있으면 바꾸지 않고 어디 있는지 알린다.
    pub fn set_encoding(&mut self, enc: Encoding) -> Res<()> {
        if enc == Encoding::Cp949 {
            if let Some((pos, c)) = crate::cp949::first_unencodable(self.buf.as_str()) {
                let (l, col) = self.line_col(pos)?;
                return Err(format!("CP949로 표현할 수 없는 글자 '{c}'(U+{:04X})가 {l}줄 {col}열에 있습니다. 그대로는 CP949로 저장할 수 없습니다.", c as u32));
            }
        }
        self.encoding = enc;
        Ok(())
    }

    /// 임시 파일 후 교체 방식으로 저장하고 깨끗한 상태로 표시한다.
    pub fn save(&mut self, path: &Path) -> Res<()> {
        let bytes = self.to_bytes()?;
        fileio::write_atomic(path, &bytes)?;
        self.path = Some(path.to_string_lossy().into_owned());
        self.mark_clean();
        Ok(())
    }

    /// 자동 저장(복구용 사본). 원본과 변경 상태는 건드리지 않는다.
    pub fn autosave(&mut self, recovery_path: &Path) -> Res<()> {
        let bytes = self.to_bytes()?;
        fileio::write_atomic(recovery_path, &bytes)
    }
}
