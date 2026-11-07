//! 간단 Markdown 해석(블록·인라인)과 서식 적용/해제 연산. 위치는 문서 전체 기준 바이트 오프셋.
//! 지원: 제목(#), 굵게(**,__), 기울임(*,_), 인라인 코드(`), 코드 블록(```), 링크([t](u)),
//! 글머리(-,*,+)/번호(1.) 목록, 인용(>), 구분선(---,***,___).

use crate::doc::{Document, Res};

#[derive(Clone, Debug, PartialEq)]
pub enum BlockKind {
    Blank,
    Paragraph,
    Heading(u8),
    Bullet { indent: usize },
    Number { n: u64, indent: usize },
    Quote,
    Rule,
    /// 코드 블록 울타리 줄(```). `open`이 참이면 여는 줄.
    Fence { lang: String, open: bool },
    Code,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum SpanKind {
    Bold,
    Italic,
    Code,
    Link,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Span {
    pub kind: SpanKind,
    /// 표지(마커) 포함 전체 범위.
    pub start: usize,
    pub end: usize,
    /// 표지를 뺀 본문 범위(링크는 글자 부분).
    pub content_start: usize,
    pub content_end: usize,
    /// 링크 주소 범위.
    pub url: Option<(usize, usize)>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Block {
    pub kind: BlockKind,
    pub line: usize,
    pub start: usize,
    pub end: usize,
    /// 줄 머리 표지(#, -, > 등) 뒤 본문 시작.
    pub content_start: usize,
    pub spans: Vec<Span>,
}

// ---------- 줄 분류 ----------

/// 줄 하나를 분류한다. `in_code`는 코드 블록 안 여부(갱신됨). 돌려주는 값은 (종류, 본문 시작 오프셋(줄 기준)).
pub fn classify(line: &str, in_code: &mut bool) -> (BlockKind, usize) {
    let trimmed = line.trim_start_matches(' ');
    let indent_bytes = line.len() - trimmed.len();
    if *in_code {
        if trimmed.starts_with("```") {
            *in_code = false;
            return (BlockKind::Fence { lang: String::new(), open: false }, line.len());
        }
        return (BlockKind::Code, 0);
    }
    if let Some(rest) = trimmed.strip_prefix("```") {
        *in_code = true;
        return (BlockKind::Fence { lang: rest.trim().to_string(), open: true }, line.len());
    }
    if line.trim().is_empty() {
        return (BlockKind::Blank, line.len());
    }
    // 제목
    let hashes = trimmed.bytes().take_while(|&b| b == b'#').count();
    if (1..=6).contains(&hashes) && indent_bytes < 4 {
        let after = &trimmed[hashes..];
        if after.is_empty() || after.starts_with(' ') {
            let skip = if after.is_empty() { 0 } else { 1 };
            return (BlockKind::Heading(hashes as u8), indent_bytes + hashes + skip);
        }
    }
    // 구분선: 같은 문자(-,*,_) 3개 이상과 공백만
    let no_space: String = trimmed.chars().filter(|c| *c != ' ').collect();
    if no_space.len() >= 3 {
        let f = no_space.chars().next().unwrap();
        if matches!(f, '-' | '*' | '_') && no_space.chars().all(|c| c == f) {
            return (BlockKind::Rule, 0);
        }
    }
    if let Some(rest) = trimmed.strip_prefix('>') {
        let skip = if rest.starts_with(' ') { 2 } else { 1 };
        return (BlockKind::Quote, indent_bytes + skip);
    }
    let b = trimmed.as_bytes();
    if b.len() >= 2 && matches!(b[0], b'-' | b'*' | b'+') && b[1] == b' ' {
        return (BlockKind::Bullet { indent: indent_bytes / 2 }, indent_bytes + 2);
    }
    let digits = b.iter().take_while(|c| c.is_ascii_digit()).count();
    if (1..=9).contains(&digits) && b.get(digits) == Some(&b'.') && b.get(digits + 1) == Some(&b' ') {
        let n = trimmed[..digits].parse().unwrap_or(1);
        return (BlockKind::Number { n, indent: indent_bytes / 2 }, indent_bytes + digits + 2);
    }
    (BlockKind::Paragraph, 0)
}

// ---------- 인라인 ----------

fn find_run(b: &[u8], from: usize, c: u8, min: usize) -> Option<(usize, usize)> {
    // from 이후 c가 min개 이상 이어진 첫 구간 [시작, 끝)
    let mut i = from;
    while i < b.len() {
        if b[i] == c {
            let s = i;
            while i < b.len() && b[i] == c {
                i += 1;
            }
            if i - s >= min {
                return Some((s, i));
            }
        } else {
            i += 1;
        }
    }
    None
}

fn is_ws(b: u8) -> bool {
    b == b' ' || b == b'\t'
}

pub fn parse_inline(s: &str, base: usize, out: &mut Vec<Span>) {
    let b = s.as_bytes();
    let mut i = 0;
    while i < b.len() {
        match b[i] {
            b'\\' => i += 2,
            b'`' => {
                let mut n = 1;
                while i + n < b.len() && b[i + n] == b'`' {
                    n += 1;
                }
                // 같은 길이의 닫는 묶음
                let mut j = i + n;
                let mut found = None;
                while let Some((rs, re)) = find_run(b, j, b'`', 1) {
                    if re - rs == n {
                        found = Some(rs);
                        break;
                    }
                    j = re;
                }
                if let Some(rs) = found.filter(|&rs| rs > i + n) {
                    out.push(Span { kind: SpanKind::Code, start: base + i, end: base + rs + n, content_start: base + i + n, content_end: base + rs, url: None });
                    i = rs + n;
                } else {
                    i += n;
                }
            }
            c @ (b'*' | b'_') => {
                let mut n = 1;
                while i + n < b.len() && b[i + n] == c {
                    n += 1;
                }
                let d = n.min(2);
                let intraword = c == b'_' && i > 0 && (b[i - 1].is_ascii_alphanumeric() || b[i - 1] >= 0x80);
                let next_ok = i + d < b.len() && !is_ws(b[i + d]);
                if intraword || !next_ok {
                    i += n;
                    continue;
                }
                // 닫는 묶음 찾기
                let mut from = i + d;
                let mut close = None;
                while let Some((rs, re)) = find_run(b, from, c, 1) {
                    let len = re - rs;
                    let prev_ok = rs > i + d && !is_ws(b[rs - 1]);
                    let tail_ok = c != b'_' || re >= b.len() || !(b[re].is_ascii_alphanumeric() || b[re] >= 0x80);
                    if prev_ok && tail_ok && ((d == 2 && len >= 2) || (d == 1 && len == 1)) {
                        close = Some(re - d);
                        break;
                    }
                    from = re;
                }
                if let Some(cs) = close {
                    let kind = if d == 2 { SpanKind::Bold } else { SpanKind::Italic };
                    out.push(Span { kind, start: base + i, end: base + cs + d, content_start: base + i + d, content_end: base + cs, url: None });
                    parse_inline(&s[i + d..cs], base + i + d, out);
                    i = cs + d;
                } else {
                    i += n;
                }
            }
            b'[' => {
                let mut j = i + 1;
                while j < b.len() && b[j] != b']' {
                    if b[j] == b'\\' {
                        j += 1;
                    }
                    j += 1;
                }
                if j + 1 < b.len() && b[j] == b']' && b[j + 1] == b'(' {
                    if let Some(k) = b[j + 2..].iter().position(|&x| x == b')') {
                        let k = j + 2 + k;
                        out.push(Span { kind: SpanKind::Link, start: base + i, end: base + k + 1, content_start: base + i + 1, content_end: base + j, url: Some((base + j + 2, base + k)) });
                        parse_inline(&s[i + 1..j], base + i + 1, out);
                        i = k + 1;
                        continue;
                    }
                }
                i += 1;
            }
            _ => i += 1,
        }
    }
}

// ---------- 문서 해석 ----------

/// 모든 줄의 "코드 블록 안" 상태를 구한다(울타리 줄 검사만 하므로 빠름).
fn fence_states(doc: &Document) -> Vec<bool> {
    let mut v = Vec::with_capacity(doc.line_count());
    let mut inside = false;
    for l in 0..doc.line_count() {
        v.push(inside);
        let (mut i, e) = (doc.line_start(l), doc.line_end(l));
        while i < e && doc.buf.byte_at(i) == b' ' {
            i += 1;
        }
        if i + 3 <= e && (0..3).all(|k| doc.buf.byte_at(i + k) == b'`') {
            inside = !inside;
        }
    }
    v
}

/// 줄 `[from_line, to_line)`을 해석한다. 코드 블록 상태는 문서 처음부터 이어서 계산한다.
pub fn parse(doc: &Document, from_line: usize, to_line: usize) -> Vec<Block> {
    let states = fence_states(doc);
    let to = to_line.min(doc.line_count());
    let mut out = Vec::new();
    for l in from_line.min(to)..to {
        let mut in_code = states[l];
        let text = doc.line_text(l);
        let (kind, off) = classify(&text, &mut in_code);
        let start = doc.line_start(l);
        let mut spans = Vec::new();
        if matches!(kind, BlockKind::Paragraph | BlockKind::Heading(_) | BlockKind::Bullet { .. } | BlockKind::Number { .. } | BlockKind::Quote) {
            parse_inline(&text[off..], start + off, &mut spans);
        }
        out.push(Block { kind, line: l, start, end: start + text.len(), content_start: start + off, spans });
    }
    out
}

/// 한 줄의 인라인 표지를 모두 뗀 평문.
pub fn strip_inline(s: &str) -> String {
    let mut spans = Vec::new();
    parse_inline(s, 0, &mut spans);
    let mut cut = vec![false; s.len()];
    for sp in &spans {
        for i in sp.start..sp.content_start {
            cut[i] = true;
        }
        for i in sp.content_end..sp.end {
            cut[i] = true;
        }
    }
    let mut out = String::with_capacity(s.len());
    for (i, c) in s.char_indices() {
        if !cut[i] {
            out.push(c);
        }
    }
    out
}

// ---------- 서식 연산 ----------

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Inline {
    Bold,
    Italic,
    Code,
}

fn run_before(doc: &Document, pos: usize, c: u8) -> usize {
    let mut n = 0;
    while n < pos && n < 3 && doc.buf.byte_at(pos - n - 1) == c {
        n += 1;
    }
    n
}
fn run_after(doc: &Document, pos: usize, c: u8) -> usize {
    let mut n = 0;
    while pos + n < doc.len() && n < 3 && doc.buf.byte_at(pos + n) == c {
        n += 1;
    }
    n
}

/// 굵게/기울임/코드를 켜고 끈다(이미 적용돼 있으면 해제). 새 선택 범위를 돌려준다.
pub fn toggle_inline(doc: &mut Document, start: usize, end: usize, kind: Inline) -> Res<(usize, usize)> {
    doc.slice(start, end)?;
    let (c, m) = match kind {
        Inline::Bold => (b'*', 2),
        Inline::Italic => (b'*', 1),
        Inline::Code => (b'`', 1),
    };
    let marker = String::from_utf8(vec![c; m]).unwrap();
    let present = |rb: usize, ra: usize| {
        let k = rb.min(ra);
        match kind {
            Inline::Bold => k >= 2,
            Inline::Italic => k % 2 == 1,
            Inline::Code => k >= 1,
        }
    };
    doc.begin_group();
    let result = (|| -> Res<(usize, usize)> {
        if start == end {
            doc.insert(start, &format!("{marker}{marker}"))?;
            return Ok((start + m, start + m));
        }
        // 선택 안에 표지가 포함된 경우(예: **글** 전체 선택)
        let sel_lead = run_after(doc, start, c);
        let sel_trail = run_before(doc, end, c);
        if end - start > sel_lead + sel_trail && present(sel_lead, sel_trail) {
            let k = m.min(sel_lead).min(sel_trail);
            doc.delete(end - k, end)?;
            doc.delete(start, start + k)?;
            return Ok((start, end - 2 * k));
        }
        // 선택 바로 바깥을 표지가 감싼 경우
        let (rb, ra) = (run_before(doc, start, c), run_after(doc, end, c));
        if present(rb, ra) {
            doc.delete(end, end + m)?;
            doc.delete(start - m, start)?;
            return Ok((start - m, end - m));
        }
        doc.insert(end, &marker)?;
        doc.insert(start, &marker)?;
        Ok((start + m, end + m))
    })();
    doc.end_group();
    result
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum BlockSet {
    Paragraph,
    Heading(u8),
    Bullet,
    Number,
    Quote,
}

fn line_range(doc: &Document, start: usize, end: usize) -> (usize, usize) {
    let first = doc.line_of(start);
    let mut last = doc.line_of(end);
    if end > start && last > first && end == doc.line_start(last) {
        last -= 1;
    }
    (first, last)
}

fn same_kind(k: &BlockKind, want: BlockSet) -> bool {
    matches!(
        (k, want),
        (BlockKind::Paragraph, BlockSet::Paragraph)
            | (BlockKind::Bullet { .. }, BlockSet::Bullet)
            | (BlockKind::Number { .. }, BlockSet::Number)
            | (BlockKind::Quote, BlockSet::Quote)
    ) || matches!((k, want), (BlockKind::Heading(a), BlockSet::Heading(b)) if *a == b)
}

/// 선택한 줄들의 문단 형식(보통·제목·목록·인용)을 바꾼다. 모든 줄이 이미 그 형식이면 "보통"으로 되돌린다.
/// 코드 블록 안의 줄은 건드리지 않는다. 바뀐 줄들 전체의 새 범위를 돌려준다.
pub fn set_block(doc: &mut Document, start: usize, end: usize, want: BlockSet) -> Res<(usize, usize)> {
    doc.slice(start, end)?;
    let (first, last) = line_range(doc, start, end);
    let states = fence_states(doc);
    let mut kinds = Vec::new();
    for l in first..=last {
        let mut in_code = states[l];
        let text = doc.line_text(l);
        kinds.push((classify(&text, &mut in_code), text));
    }
    let targets: Vec<_> = kinds.iter().filter(|((k, _), _)| !matches!(k, BlockKind::Code | BlockKind::Fence { .. } | BlockKind::Blank)).collect();
    let all_same = !targets.is_empty() && targets.iter().all(|((k, _), _)| same_kind(k, want));
    let eff = if all_same { BlockSet::Paragraph } else { want };
    let mut n = 0u64;
    let mut lines = Vec::new();
    for ((k, off), text) in &kinds {
        if matches!(k, BlockKind::Code | BlockKind::Fence { .. } | BlockKind::Blank | BlockKind::Rule) {
            lines.push(text.clone());
            continue;
        }
        let body = match k {
            BlockKind::Paragraph => text.as_str(),
            _ => &text[*off..],
        };
        lines.push(match eff {
            BlockSet::Paragraph => body.to_string(),
            BlockSet::Heading(l) => format!("{} {}", "#".repeat(l.clamp(1, 6) as usize), body),
            BlockSet::Bullet => format!("- {body}"),
            BlockSet::Number => {
                n += 1;
                format!("{n}. {body}")
            }
            BlockSet::Quote => format!("> {body}"),
        });
    }
    let (s, e) = (doc.line_start(first), doc.line_end(last));
    let joined = lines.join("\n");
    doc.replace_range(s, e, &joined)?;
    doc.commit();
    Ok((s, s + joined.len()))
}

/// `[글자](주소)` 링크로 바꾼다. 선택이 없으면 주소를 글자로 쓴다. 새 선택(글자 부분)을 돌려준다.
pub fn insert_link(doc: &mut Document, start: usize, end: usize, url: &str) -> Res<(usize, usize)> {
    let sel = doc.slice(start, end)?;
    let label = if sel.is_empty() { url.to_string() } else { sel };
    doc.begin_group();
    let r = doc.replace_range(start, end, &format!("[{label}]({url})"));
    doc.end_group();
    r?;
    Ok((start + 1, start + 1 + label.len()))
}

/// 현재 줄 아래에 구분선(---)을 넣고 커서를 그 다음 줄로 보낸다.
pub fn insert_rule(doc: &mut Document, pos: usize) -> Res<usize> {
    doc.slice(pos, pos)?;
    let line = doc.line_of(pos);
    let at = doc.line_end(line);
    let blank = doc.line_text(line).trim().is_empty();
    let ins = if blank { "---\n" } else { "\n---\n" };
    let r = doc.insert(at, ins);
    doc.commit();
    r
}

/// 선택한 줄들을 ``` 울타리로 감싸거나(코드 블록), 이미 감싸져 있으면 울타리를 없앤다.
pub fn toggle_code_block(doc: &mut Document, start: usize, end: usize) -> Res<(usize, usize)> {
    doc.slice(start, end)?;
    let (first, last) = line_range(doc, start, end);
    let wrapped = last > first && {
        let is_fence = |l: usize| doc.line_text(l).trim_start_matches(' ').starts_with("```");
        is_fence(first) && is_fence(last)
    };
    doc.begin_group();
    let res = (|| -> Res<(usize, usize)> {
        if wrapped {
            // 아래 울타리 줄부터 지운다(앞 줄 위치가 변하지 않게).
            let (ls, le) = (doc.line_start(last), doc.line_end(last));
            doc.delete(ls.saturating_sub(1), le)?;
            let (fs, fe) = (doc.line_start(first), doc.line_end(first));
            doc.delete(fs, (fe + 1).min(doc.len()))?;
            let s = doc.line_start(first);
            let content = last - first - 1;
            Ok((s, if content == 0 { s } else { doc.line_end(first + content - 1) }))
        } else {
            let le = doc.line_end(last);
            doc.insert(le, "\n```")?;
            let fs = doc.line_start(first);
            doc.insert(fs, "```\n")?;
            Ok((doc.line_start(first + 1), doc.line_end(last + 1)))
        }
    })();
    doc.end_group();
    res
}

/// 선택한 줄들의 서식(제목·목록·인용·굵게 등 모든 표지와 코드 울타리)을 지워 평문으로 만든다.
pub fn clear_format(doc: &mut Document, start: usize, end: usize) -> Res<(usize, usize)> {
    doc.slice(start, end)?;
    let (first, last) = line_range(doc, start, end);
    let states = fence_states(doc);
    let mut lines: Vec<String> = Vec::new();
    for l in first..=last {
        let mut in_code = states[l];
        let text = doc.line_text(l);
        let (k, off) = classify(&text, &mut in_code);
        match k {
            BlockKind::Fence { .. } => {}
            BlockKind::Code | BlockKind::Blank | BlockKind::Rule => lines.push(text),
            BlockKind::Paragraph => lines.push(strip_inline(&text)),
            _ => lines.push(strip_inline(&text[off..])),
        }
    }
    let (s, e) = (doc.line_start(first), doc.line_end(last));
    let joined = lines.join("\n");
    doc.replace_range(s, e, &joined)?;
    doc.commit();
    Ok((s, s + joined.len()))
}
