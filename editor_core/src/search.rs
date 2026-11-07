//! 찾기·바꾸기 (대소문자 옵션, 온전한 낱말 옵션). 위치는 바이트 오프셋.

#[derive(Clone, Copy, Debug)]
pub struct SearchOpts {
    pub case_sensitive: bool,
    pub whole_word: bool,
}

fn fold(c: char) -> char {
    let mut it = c.to_lowercase();
    match (it.next(), it.next()) {
        (Some(l), None) => l,
        _ => c,
    }
}

fn is_word(c: char) -> bool {
    c.is_alphanumeric() || c == '_'
}

fn word_ok(text: &str, s: usize, e: usize) -> bool {
    let before = text[..s].chars().next_back().is_none_or(|c| !is_word(c));
    let after = text[e..].chars().next().is_none_or(|c| !is_word(c));
    before && after
}

/// `from` 이후 첫 일치. 일치 구간 `(start,end)`를 돌려준다.
pub fn find_next(text: &str, query: &str, from: usize, o: SearchOpts) -> Option<(usize, usize)> {
    if query.is_empty() || from > text.len() || !text.is_char_boundary(from) {
        return None;
    }
    if o.case_sensitive {
        let mut at = from;
        while let Some(i) = text[at..].find(query) {
            let s = at + i;
            let e = s + query.len();
            if !o.whole_word || word_ok(text, s, e) {
                return Some((s, e));
            }
            at = s + text[s..].chars().next().map_or(1, |c| c.len_utf8());
        }
        return None;
    }
    let needle: Vec<char> = query.chars().map(fold).collect();
    let mut it = text[from..].char_indices().map(|(i, c)| (from + i, c)).peekable();
    while let Some(&(s, c)) = it.peek() {
        it.next();
        if fold(c) != needle[0] {
            continue;
        }
        let mut probe = text[s..].char_indices().map(|(i, c)| (s + i, c));
        let mut end = s;
        let mut ok = true;
        for &n in &needle {
            match probe.next() {
                Some((i, h)) if fold(h) == n => end = i + h.len_utf8(),
                _ => {
                    ok = false;
                    break;
                }
            }
        }
        if ok && (!o.whole_word || word_ok(text, s, end)) {
            return Some((s, end));
        }
    }
    None
}

/// 겹치지 않는 모든 일치(최대 `limit`개).
pub fn find_all(text: &str, query: &str, o: SearchOpts, limit: usize) -> Vec<(usize, usize)> {
    let mut v = Vec::new();
    let mut at = 0;
    while v.len() < limit {
        let Some((s, e)) = find_next(text, query, at, o) else { break };
        v.push((s, e));
        at = e;
    }
    v
}

/// 바꾼 결과 문자열과 바꾼 개수. 변경이 없으면 `None`.
pub fn replace_all_text(text: &str, query: &str, with: &str, o: SearchOpts) -> Option<(String, usize)> {
    let hits = find_all(text, query, o, usize::MAX);
    if hits.is_empty() {
        return None;
    }
    let mut out = String::with_capacity(text.len());
    let mut last = 0;
    for &(s, e) in &hits {
        out.push_str(&text[last..s]);
        out.push_str(with);
        last = e;
    }
    out.push_str(&text[last..]);
    Some((out, hits.len()))
}
