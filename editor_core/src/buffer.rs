//! 갭 버퍼 기반 텍스트 버퍼. 모든 위치는 UTF-8 바이트 오프셋이며 글자 경계만 허용한다.
//! 내부 줄바꿈은 항상 `\n`(LF). 줄 시작 색인과 글자 수를 편집마다 점진 갱신한다.

pub struct TextBuffer {
    buf: Vec<u8>,
    gs: usize,
    ge: usize,
    line_starts: Vec<usize>,
    chars: usize,
}

impl Default for TextBuffer {
    fn default() -> Self {
        Self::new()
    }
}

impl TextBuffer {
    pub fn new() -> Self {
        TextBuffer { buf: Vec::new(), gs: 0, ge: 0, line_starts: vec![0], chars: 0 }
    }

    pub fn from_str(s: &str) -> Self {
        let mut b = TextBuffer::new();
        b.insert(0, s);
        b
    }

    pub fn len(&self) -> usize {
        self.buf.len() - (self.ge - self.gs)
    }
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
    /// 유니코드 스칼라(글자) 수.
    pub fn char_count(&self) -> usize {
        self.chars
    }

    pub fn byte_at(&self, i: usize) -> u8 {
        if i < self.gs { self.buf[i] } else { self.buf[i + (self.ge - self.gs)] }
    }

    pub fn is_char_boundary(&self, i: usize) -> bool {
        let n = self.len();
        i == 0 || i == n || (i < n && (self.byte_at(i) & 0xC0) != 0x80)
    }

    fn move_gap(&mut self, pos: usize) {
        if pos < self.gs {
            let n = self.gs - pos;
            self.buf.copy_within(pos..self.gs, self.ge - n);
            self.gs = pos;
            self.ge -= n;
        } else if pos > self.gs {
            let n = pos - self.gs;
            self.buf.copy_within(self.ge..self.ge + n, self.gs);
            self.gs += n;
            self.ge += n;
        }
    }

    fn ensure_gap(&mut self, need: usize) {
        let gap = self.ge - self.gs;
        if gap >= need {
            return;
        }
        let extra = (need - gap).max(self.len() / 2 + 256);
        let old = self.buf.len();
        self.buf.resize(old + extra, 0);
        self.buf.copy_within(self.ge..old, self.ge + extra);
        self.ge += extra;
    }

    /// `pos`에 삽입한다. `pos`는 글자 경계여야 하고 `s`에는 `\r`가 없어야 한다(호출자 보장).
    pub fn insert(&mut self, pos: usize, s: &str) {
        if s.is_empty() {
            return;
        }
        debug_assert!(self.is_char_boundary(pos));
        self.ensure_gap(s.len());
        self.move_gap(pos);
        self.buf[self.gs..self.gs + s.len()].copy_from_slice(s.as_bytes());
        self.gs += s.len();
        self.chars += s.chars().count();
        let idx = self.line_starts.partition_point(|&x| x <= pos);
        for x in &mut self.line_starts[idx..] {
            *x += s.len();
        }
        let new: Vec<usize> = s.match_indices('\n').map(|(i, _)| pos + i + 1).collect();
        if !new.is_empty() {
            self.line_starts.splice(idx..idx, new);
        }
    }

    /// `[start,end)`를 지우고 지운 문자열을 돌려준다.
    pub fn delete(&mut self, start: usize, end: usize) -> String {
        if start >= end {
            return String::new();
        }
        let removed = self.slice(start, end);
        self.move_gap(start);
        self.ge += end - start;
        self.chars -= removed.chars().count();
        let lo = self.line_starts.partition_point(|&x| x <= start);
        let hi = self.line_starts.partition_point(|&x| x <= end);
        self.line_starts.drain(lo..hi);
        for x in &mut self.line_starts[lo..] {
            *x -= end - start;
        }
        removed
    }

    pub fn slice(&self, start: usize, end: usize) -> String {
        let mut v = Vec::with_capacity(end - start);
        let g = self.ge - self.gs;
        if end <= self.gs {
            v.extend_from_slice(&self.buf[start..end]);
        } else if start >= self.gs {
            v.extend_from_slice(&self.buf[start + g..end + g]);
        } else {
            v.extend_from_slice(&self.buf[start..self.gs]);
            v.extend_from_slice(&self.buf[self.ge..end + g]);
        }
        String::from_utf8(v).expect("글자 경계 보장 위반")
    }

    /// 전체를 연속 메모리로 만들어 `&str`로 돌려준다(갭을 끝으로 옮김).
    pub fn as_str(&mut self) -> &str {
        let n = self.len();
        self.move_gap(n);
        std::str::from_utf8(&self.buf[..n]).expect("글자 경계 보장 위반")
    }

    // ---- 줄 색인 ----
    pub fn line_count(&self) -> usize {
        self.line_starts.len()
    }
    /// 0부터 센 줄 번호의 시작 오프셋.
    pub fn line_start(&self, line: usize) -> usize {
        self.line_starts[line.min(self.line_starts.len() - 1)]
    }
    /// 줄 끝(개행 직전) 오프셋.
    pub fn line_end(&self, line: usize) -> usize {
        if line + 1 < self.line_starts.len() { self.line_starts[line + 1] - 1 } else { self.len() }
    }
    pub fn line_of(&self, pos: usize) -> usize {
        self.line_starts.partition_point(|&x| x <= pos) - 1
    }
    /// `[start,end)`의 글자 수.
    pub fn count_chars(&self, start: usize, end: usize) -> usize {
        (start..end).filter(|&i| (self.byte_at(i) & 0xC0) != 0x80).count()
    }
}
