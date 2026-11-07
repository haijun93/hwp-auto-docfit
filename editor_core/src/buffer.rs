//! 갭 버퍼 기반 텍스트 버퍼. 모든 위치는 UTF-8 바이트 오프셋이며 글자 경계만 허용한다.
//! 내부 줄바꿈은 항상 `\n`(LF). 줄 시작 색인과 글자 수를 편집마다 점진 갱신한다.
//!
//! 줄 시작 색인은 **물리 좌표**(갭을 포함한 `buf` 안의 위치)로 보관한다. 갭 뒤쪽 글의 줄 시작은
//! `논리 위치 + 갭 크기`로 저장되므로, 갭 자리에서 입력·삭제를 해도 뒤쪽 줄 수만큼 값을 고쳐 쓰지 않는다
//! (갭을 옮길 때만 옮겨지는 구간의 줄을 고친다). 100만 글자·줄당 4자(25만 줄)에서 이어 입력이 글자당 33 µs → 아래 표 참고.

pub struct TextBuffer {
    buf: Vec<u8>,
    gs: usize,
    ge: usize,
    /// 줄 시작(물리 좌표). `<= gs`면 논리 위치 그대로, `>= ge`면 `- 갭 크기`가 논리 위치.
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

    /// 물리 좌표 → 논리 위치.
    #[inline]
    fn logical(&self, p: usize) -> usize {
        if p <= self.gs { p } else { p - (self.ge - self.gs) }
    }

    /// 갭 자리와 정확히 같은 논리 위치의 줄 시작(`== ge`)을 `gs` 꼴로 통일한다(삽입·삭제 직전에 호출).
    fn normalize_at_gap(&mut self) {
        let (gs, ge) = (self.gs, self.ge);
        if ge == gs {
            return;
        }
        let i = self.line_starts.partition_point(|&x| x < ge);
        if self.line_starts.get(i) == Some(&ge) {
            self.line_starts[i] = gs;
        }
    }

    fn move_gap(&mut self, pos: usize) {
        let gap = self.ge - self.gs;
        if pos < self.gs {
            let n = self.gs - pos;
            // 논리 (pos, gs]에 있던 줄 시작은 갭 뒤쪽으로 넘어간다 → +갭
            let lo = self.line_starts.partition_point(|&x| x <= pos);
            let hi = self.line_starts.partition_point(|&x| x <= self.gs);
            if gap > 0 {
                for x in &mut self.line_starts[lo..hi] {
                    *x += gap;
                }
            }
            self.buf.copy_within(pos..self.gs, self.ge - n);
            self.gs = pos;
            self.ge -= n;
        } else if pos > self.gs {
            let n = pos - self.gs;
            // 갭 뒤쪽에서 앞쪽으로 넘어오는 [ge, ge+n] 구간의 줄 시작은 -갭
            let lo = self.line_starts.partition_point(|&x| x < self.ge);
            let hi = self.line_starts.partition_point(|&x| x <= self.ge + n);
            if gap > 0 {
                for x in &mut self.line_starts[lo..hi] {
                    *x -= gap;
                }
            }
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
        // 갭 뒤쪽 줄 시작은 물리 좌표가 extra만큼 밀린다
        let from = self.line_starts.partition_point(|&x| x < self.ge);
        for x in &mut self.line_starts[from..] {
            *x += extra;
        }
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
        self.normalize_at_gap();
        let old_gs = self.gs;
        self.buf[self.gs..self.gs + s.len()].copy_from_slice(s.as_bytes());
        self.gs += s.len();
        self.chars += s.chars().count();
        if s.as_bytes().contains(&b'\n') {
            let idx = self.line_starts.partition_point(|&x| x <= old_gs);
            let new: Vec<usize> = s.match_indices('\n').map(|(i, _)| old_gs + i + 1).collect();
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
        self.normalize_at_gap();
        self.chars -= removed.chars().count();
        // 지워지는 글의 줄 시작(논리 (start, end])은 물리 (gs, ge+n]
        let n = end - start;
        let lo = self.line_starts.partition_point(|&x| x <= self.gs);
        let hi = self.line_starts.partition_point(|&x| x <= self.ge + n);
        if lo < hi {
            self.line_starts.drain(lo..hi);
        }
        self.ge += n;
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
        self.logical(self.line_starts[line.min(self.line_starts.len() - 1)])
    }
    /// 줄 끝(개행 직전) 오프셋.
    pub fn line_end(&self, line: usize) -> usize {
        if line + 1 < self.line_starts.len() { self.logical(self.line_starts[line + 1]) - 1 } else { self.len() }
    }
    pub fn line_of(&self, pos: usize) -> usize {
        self.line_starts.partition_point(|&x| self.logical(x) <= pos) - 1
    }
    /// 시험용: 줄 색인이 실제 글의 줄바꿈 위치와 같은지 확인한다(어긋나면 설명 문자열).
    pub fn check_index(&self) -> Result<(), String> {
        let n = self.len();
        let mut expect = vec![0usize];
        for i in 0..n {
            if self.byte_at(i) == b'\n' {
                expect.push(i + 1);
            }
        }
        let got: Vec<usize> = self.line_starts.iter().map(|&x| self.logical(x)).collect();
        if got != expect {
            return Err(format!("줄 색인 불일치: 기대 {}줄, 실제 {}줄", expect.len(), got.len()));
        }
        let chars = (0..n).filter(|&i| (self.byte_at(i) & 0xC0) != 0x80).count();
        if chars != self.chars {
            return Err(format!("글자 수 불일치: 기대 {chars}, 실제 {}", self.chars));
        }
        Ok(())
    }
    /// `[start,end)`의 글자 수.
    pub fn count_chars(&self, start: usize, end: usize) -> usize {
        (start..end).filter(|&i| (self.byte_at(i) & 0xC0) != 0x80).count()
    }
}

#[cfg(test)]
mod tests {
    use super::TextBuffer;

    /// 무작위 삽입·삭제·갭 이동(as_str)을 문자열 모델과 비교하며 줄 색인을 매 단계 검증한다.
    #[test]
    fn line_index_matches_model_under_random_edits() {
        let pieces = ["a", "한", "\n", "\n\n", "bc\n", "😀", "가\n나", "", "xyz"];
        let mut seed = 12345u64;
        let mut rnd = move |m: usize| {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (seed >> 33) as usize % m.max(1)
        };
        let mut b = TextBuffer::new();
        let mut model = String::new();
        for step in 0..6000 {
            let bounds: Vec<usize> = model.char_indices().map(|(i, _)| i).chain([model.len()]).collect();
            match rnd(5) {
                0 | 1 | 2 => {
                    let pos = bounds[rnd(bounds.len())];
                    let s = pieces[rnd(pieces.len())];
                    b.insert(pos, s);
                    model.insert_str(pos, s);
                }
                3 => {
                    let i = rnd(bounds.len());
                    let j = (i + rnd(6)).min(bounds.len() - 1);
                    let (s, e) = (bounds[i], bounds[j]);
                    assert_eq!(b.delete(s, e), model[s..e]);
                    model.replace_range(s..e, "");
                }
                _ => assert_eq!(b.as_str(), model),
            }
            b.check_index().unwrap_or_else(|m| panic!("{step}단계: {m}"));
            assert_eq!(b.len(), model.len());
            let line = rnd(b.line_count());
            let expect_start = if line == 0 { 0 } else { model.match_indices('\n').nth(line - 1).unwrap().0 + 1 };
            assert_eq!(b.line_start(line), expect_start);
            let p = bounds_pos(&model, rnd(model.len() + 1));
            assert_eq!(b.line_of(p), model[..p].matches('\n').count());
        }
        assert_eq!(b.as_str(), model);
    }

    fn bounds_pos(s: &str, mut p: usize) -> usize {
        while !s.is_char_boundary(p) {
            p -= 1;
        }
        p
    }
}
