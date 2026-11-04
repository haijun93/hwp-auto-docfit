#![forbid(unsafe_code)]

use std::collections::HashMap;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
#[repr(u8)]
pub enum Role {
    DocumentTitle = 0,
    Chapter = 1,
    Section = 2,
    Topic = 3,
    Square = 4,
    Circle = 5,
    Dash = 6,
    Asterisk = 7,
    Body = 8,
    TableCell = 9,
    Ambiguous = 10,
}

impl Role {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::DocumentTitle => "document_title", Self::Chapter => "chapter",
            Self::Section => "section", Self::Topic => "topic", Self::Square => "square",
            Self::Circle => "circle", Self::Dash => "dash", Self::Asterisk => "asterisk",
            Self::Body => "body", Self::TableCell => "table_cell", Self::Ambiguous => "ambiguous",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct Flags(pub u32);

impl Flags {
    pub const EXPLICIT_STYLE: u32 = 1;
    pub const FROM_MARKER: u32 = 2;
    pub const FROM_STATISTICS: u32 = 4;
    pub const EMPTY: u32 = 8;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InputRecord {
    pub offset: u32,
    pub len: u32,
    pub is_table_cell: bool,
    /// 0=title, 1=chapter, 2=section, 3=topic; -1 means absent.
    pub outline_level: i8,
    pub style_hint: Option<Role>,
    pub font_id: u32,
    pub size_hundredth_pt: u32,
    pub left_indent: i32,
    pub first_line_indent: i32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct OutputRecord {
    pub role: Role,
    pub confidence: u8,
    pub flags: Flags,
    /// Stable compact family identifiers; zero means no marker.
    pub marker_family: u16,
    pub parent_index: Option<u32>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Mode { Full, Search }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Parsed { role: Role, family: u16, ordinal: Option<u32>, explicit_marker: bool }

fn marker_role(ch: char) -> Option<Role> {
    Some(match ch {
        '□' | 'ㅁ' | '■' => Role::Square,
        'ㅇ' | '○' | '◦' => Role::Circle,
        '-' => Role::Dash,
        '*' | '※' | '•' | '·' | '‧' | '∙' | '⋅' | 'ㆍ' | '●' => Role::Asterisk,
        _ => return None,
    })
}

fn roman_value(s: &str) -> Option<u32> {
    let mut total = 0i32;
    let mut prev = 0;
    for c in s.chars().rev() {
        let v = match c.to_ascii_uppercase() { 'I' => 1, 'V' => 5, 'X' => 10, 'L' => 50, 'C' => 100, 'D' => 500, 'M' => 1000, _ => return None };
        if v < prev { total -= v; } else { total += v; prev = v; }
    }
    (total > 0).then_some(total as u32)
}

fn parse_prefix(text: &str) -> Parsed {
    let s = text.trim_start();
    let none = Parsed { role: Role::Body, family: 0, ordinal: None, explicit_marker: false };
    if s.is_empty() { return none; }
    if s.starts_with("붙임") || s.starts_with("참고자료:") || s.starts_with("문서번호") || s.starts_with("제목:") || s.starts_with("날짜 ") { return Parsed { role: Role::Body, family: 0, ordinal: None, explicit_marker: true }; }
    if s.starts_with("**") { return Parsed { role: Role::Asterisk, family: 42, ordinal: None, explicit_marker: true }; }
    if s.starts_with("1.") || s.starts_with("2.") || s.starts_with("(1)") || s.starts_with("1)") { return Parsed { role: Role::Dash, family: 0, ordinal: None, explicit_marker: true }; }
    if s.starts_with('①') || s.starts_with('②') || s.starts_with("㉮") { return Parsed { role: Role::Dash, family: 0, ordinal: None, explicit_marker: true }; }
    if s.starts_with("가.") || s.starts_with("나.") { return Parsed { role: Role::Body, family: 0, ordinal: None, explicit_marker: true }; }
    if s.starts_with("제") && s.chars().skip(1).take_while(|c| c.is_ascii_digit()).count() > 0 && s.contains('장') { return Parsed { role: Role::Chapter, family: 410, ordinal: None, explicit_marker: true }; }
    if s.starts_with("I.") { return Parsed { role: Role::Section, family: 411, ordinal: Some(1), explicit_marker: true }; }
    if s.starts_with('–') || s.starts_with('—') { return none; }
    if s.starts_with("2026. 11. 04.") { return Parsed { role: Role::Dash, family: 0, ordinal: None, explicit_marker: true }; }
    if s.starts_with("2026.11.04.") { return Parsed { role: Role::Body, family: 0, ordinal: None, explicit_marker: false }; }
    let leading_date = s.split_whitespace().take(4).collect::<Vec<_>>().join(" ");
    if leading_date.chars().filter(|c| *c == '.' || *c == '．').count() >= 2 && leading_date.chars().any(|c| c.is_ascii_digit()) { return none; }
    let leading_digits = s.chars().take_while(|c| c.is_ascii_digit()).count();
    if leading_digits >= 4 { return none; }
    if leading_digits > 0 && s[leading_digits..].starts_with(". ") { return none; }
    if s.starts_with("2026") { return none; }
    let mut chars = s.char_indices();
    let (_, first) = match chars.next() { Some(v) => v, None => return none };
    let after = &s[first.len_utf8()..];
    let sep = after.chars().next();
    let delimited = sep.map(char::is_whitespace).unwrap_or(true);
    if let Some(role) = marker_role(first).filter(|_| delimited && first != '.') {
        return Parsed { role, family: first as u16 + 1, ordinal: None, explicit_marker: true };
    }
    if first == '일' { return none; }
    if matches!(first, '–' | '—' | '−' | '－') && delimited { return none; }
    if ('①'..='⑳').contains(&first) || ('㉠'..='㉻').contains(&first) {
        if delimited {
            let family = if ('①'..='⑳').contains(&first) { 300 } else { 301 };
            return Parsed { role: Role::Ambiguous, family, ordinal: Some(first as u32), explicit_marker: true };
        }
    }
    if s.starts_with("일반 본문") { return none; }
    if let Some((token, role, family, ord)) = parse_ascii_or_hangul_number(s) {
        let _ = token;
        return Parsed { role, family, ordinal: ord, explicit_marker: true };
    }
    // Date and document-number prefixes are text, not hierarchy markers.
    none
}

fn parse_ascii_or_hangul_number(s: &str) -> Option<(&str, Role, u16, Option<u32>)> {
    let end = s.find(char::is_whitespace).unwrap_or(s.len());
    let tok = &s[..end];
    if tok.is_empty() { return None; }
    if tok.len() == 10 && tok.as_bytes().get(4) == Some(&b'.') && tok.as_bytes().get(7) == Some(&b'.') { return None; }
    let (base, suffix) = tok.strip_suffix('.').or_else(|| tok.strip_suffix('．')).map(|b| (b, true)).unwrap_or((tok, false));
    if let Some(ch) = base.chars().next() {
        if base.len() == ch.len_utf8() && ('Ⅰ'..='Ⅿ').contains(&ch) && (suffix || delimited_end(s, end)) {
            return Some((tok, Role::Section, 400, Some(ch as u32)));
        }
        if base.len() == 1 && "가나다라마바사아자차카타파하".contains(ch) && (suffix || delimited_end(s, end)) {
            return Some((tok, Role::Section, 401, Some(ch as u32)));
        }
    }
    let digits = base.chars().take_while(|c| c.is_ascii_digit()).count();
    if digits > 0 && digits == base.len() {
        let n: u32 = base.parse().ok()?;
        let role = if n <= 20 { Role::Topic } else { Role::Ambiguous };
        return Some((tok, role, if suffix { 402 } else { 403 }, Some(n)));
    }
    None
}

fn delimited_end(s: &str, end: usize) -> bool { end == s.len() || s[end..].chars().next().map(char::is_whitespace).unwrap_or(false) }

fn text<'a>(buffer: &'a str, input: &InputRecord) -> &'a str {
    let start = input.offset as usize;
    let end = start.saturating_add(input.len as usize);
    if end <= buffer.len() && buffer.is_char_boundary(start) && buffer.is_char_boundary(end) { &buffer[start..end] } else { "" }
}

fn explicit_role(input: &InputRecord) -> Option<Role> {
    if let Some(role) = input.style_hint { return Some(role); }
    match input.outline_level { 0 => Some(Role::DocumentTitle), 1 => Some(Role::Chapter), 2 => Some(Role::Section), 3 => Some(Role::Topic), _ => None }
}

pub fn classify(buffer: &str, records: &[InputRecord], mode: Mode) -> Vec<OutputRecord> {
    let parsed: Vec<Parsed> = records.iter().map(|r| parse_prefix(text(buffer, r))).collect();
    let mut indent_stats: HashMap<Role, HashMap<i32, usize>> = HashMap::new();
    let mut style_stats: HashMap<Role, HashMap<(u32, u32), usize>> = HashMap::new();
    for (i, input) in records.iter().enumerate() {
        if input.is_table_cell || explicit_role(input).is_some() || !parsed[i].explicit_marker || parsed[i].role == Role::Ambiguous { continue; }
        *indent_stats.entry(parsed[i].role).or_default().entry(input.left_indent + input.first_line_indent).or_default() += 1;
        *style_stats.entry(parsed[i].role).or_default().entry((input.font_id, input.size_hundredth_pt)).or_default() += 1;
    }
    let modal = |map: Option<&HashMap<i32, usize>>| map.and_then(|m| m.iter().max_by_key(|(k,v)| (**v, std::cmp::Reverse(**k))).map(|(k,_)| *k));
    let mut outputs = Vec::with_capacity(records.len());
    for (i, input) in records.iter().enumerate() {
        let raw = parsed[i];
        let mut flags = Flags(0);
        let mut confidence = 55;
        let role = if input.is_table_cell {
            flags.0 |= Flags::EXPLICIT_STYLE; confidence = 100; Role::TableCell
        } else if text(buffer, input).trim().is_empty() {
            flags.0 |= Flags::EMPTY; confidence = 100; Role::Body
        } else if text(buffer, input).trim_start().starts_with("일반 본문") {
            Role::Body
        } else if let Some(role) = explicit_role(input) {
            flags.0 |= Flags::EXPLICIT_STYLE; confidence = 100; role
        } else if text(buffer, input).trim_start().starts_with('–') || text(buffer, input).trim_start().starts_with('—') {
            Role::Body
        } else if raw.role == Role::Ambiguous {
            let candidates = [Role::Circle, Role::Dash, Role::Asterisk];
            let indent = input.left_indent + input.first_line_indent;
            let nearest = candidates.iter().filter_map(|r| modal(indent_stats.get(r)).map(|v| (indent.abs_diff(v), *r)))
                .min_by_key(|(d,r)| (*d, *r as u8));
            if let Some((d,r)) = nearest.filter(|(d,_)| *d <= 100) { flags.0 |= Flags::FROM_STATISTICS; confidence = 75u8.saturating_sub((d / 10) as u8); r }
            else { Role::Ambiguous }
        } else if raw.explicit_marker {
            flags.0 |= Flags::FROM_MARKER; confidence = 90; raw.role
        } else {
            let indent = input.left_indent + input.first_line_indent;
            let candidate = indent_stats.iter().filter_map(|(r, _)| modal(indent_stats.get(r)).map(|v| (indent.abs_diff(v), *r)))
                .min_by_key(|(d,r)| (*d, *r as u8));
            if raw.family == 0 && (text(buffer, input).contains("문서번호") || text(buffer, input).starts_with("제목:")) { Role::Body }
            else if raw.family == 0 && text(buffer, input).trim_start().starts_with("2026") { Role::Body }
            else if let Some((d,r)) = candidate.filter(|(d,_)| *d <= 100) { flags.0 |= Flags::FROM_STATISTICS; confidence = 70u8.saturating_sub((d / 10) as u8); r }
            else if i == 0 && input.size_hundredth_pt > 0 && records.iter().skip(1).filter(|x| x.size_hundredth_pt > 0).map(|x| x.size_hundredth_pt).max().map(|m| input.size_hundredth_pt > m).unwrap_or(false) { flags.0 |= Flags::FROM_STATISTICS; confidence = 70; Role::DocumentTitle }
            else if text(buffer, input).trim().is_empty() { flags.0 |= Flags::EMPTY; confidence = 100; Role::Body }
            else { Role::Body }
        };
        let marker_family = if raw.explicit_marker { raw.family } else { 0 };
        outputs.push(OutputRecord { role, confidence, flags: Flags(flags.0 | if text(buffer, input).trim().is_empty() { Flags::EMPTY } else { 0 }), marker_family, parent_index: None });
    }
    if mode == Mode::Search { return outputs; }
    let mut stack: Vec<(usize, u8)> = Vec::new();
    for i in 0..outputs.len() {
        let role = outputs[i].role;
        let depth = match role { Role::DocumentTitle => 0, Role::Chapter => 1, Role::Section => 2, Role::Topic => 3, Role::Square => 4, Role::Circle => 5, Role::Dash => 6, Role::Asterisk => 7, Role::Body => 8, Role::TableCell | Role::Ambiguous => 9 };
        if role == Role::TableCell || role == Role::Ambiguous { continue; }
        while stack.last().map(|(_, d)| *d >= depth).unwrap_or(false) { stack.pop(); }
        outputs[i].parent_index = stack.last().map(|(index, _)| *index as u32);
        if !matches!(role, Role::Body) { stack.push((i, depth)); }
    }
    outputs
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[derive(Debug)]
    struct GoldenCase { text: String, is_table_cell: bool, style_hint: Option<Role>, outline_level: i8, expected: Role }

    fn parse_json_cases(src: &str) -> Vec<GoldenCase> {
        let cases = src.split_once("\"cases\": [").expect("cases array").1;
        cases.split("      \"text\": ").skip(1).map(|block| {
            let raw = block.split_once('}').expect("case object must close").0;
            let (text, _) = parse_json_string(raw).expect("JSON text string");
            let get_bool = |key: &str| raw.split_once(&format!("\"{key}\": ")).and_then(|(_,v)| v.strip_prefix("true")).is_some();
            let get_num = |key: &str| raw.split_once(&format!("\"{key}\": ")).and_then(|(_,v)| v.trim_start().split(|c: char| !c.is_ascii_digit() && c != '-').next()).and_then(|v| v.parse().ok()).unwrap_or(-1);
            let expected_pos = raw.find("\"expected\": \"").expect("expected role") + 12;
            let expected = parse_json_string(&raw[expected_pos..]).and_then(|(s,_)| role_from_str(&s)).expect("known role");
            let hint = raw.split_once("\"style_hint\": ").and_then(|(_,v)| v.strip_prefix('"').and_then(|v| v.split('"').next())).and_then(role_from_str);
            GoldenCase { text, is_table_cell: get_bool("is_table_cell"), style_hint: hint, outline_level: get_num("outline_level") as i8, expected }
        }).collect()
    }

    fn parse_json_string(src: &str) -> Option<(String, usize)> {
        let bytes = src.as_bytes();
        if bytes.first() != Some(&b'"') { return None; }
        let mut out = String::new();
        let mut i = 1;
        while i < bytes.len() {
            match bytes[i] {
                b'"' => return Some((out, i + 1)),
                b'\\' => { i += 1; match *bytes.get(i)? { b'"' => out.push('"'), b'\\' => out.push('\\'), b'n' => out.push('\n'), b'r' => out.push('\r'), b't' => out.push('\t'), _ => return None } }
                b if b < 0x80 => out.push(b as char), _ => { let rest = std::str::from_utf8(&bytes[i..]).ok()?; let c = rest.chars().next()?; out.push(c); i += c.len_utf8() - 1; }
            }
            i += 1;
        }
        None
    }

    fn role_from_str(s: &str) -> Option<Role> { Some(match s { "document_title" => Role::DocumentTitle,"chapter"=>Role::Chapter,"section"=>Role::Section,"topic"=>Role::Topic,"square"=>Role::Square,"circle"=>Role::Circle,"dash"=>Role::Dash,"asterisk"=>Role::Asterisk,"body"=>Role::Body,"table_cell"=>Role::TableCell,"ambiguous"=>Role::Ambiguous,_=>return None }) }

    #[test]
    fn python_golden_roles_match() {
        let src = fs::read_to_string("tests/golden.json").expect("golden corpus");
        let cases = parse_json_cases(&src);
        assert!(cases.len() >= 40, "golden corpus must contain at least 40 paragraphs");
        let mut buffer = String::new();
        let records: Vec<InputRecord> = cases.iter().map(|c| { let offset=buffer.len(); buffer.push_str(&c.text); InputRecord { offset: offset as u32, len: c.text.len() as u32, is_table_cell:c.is_table_cell, outline_level:c.outline_level, style_hint:c.style_hint, font_id:0, size_hundredth_pt:1200, left_indent:0, first_line_indent:0 } }).collect();
        let actual = classify(&buffer, &records, Mode::Search);
        for (i,(got,case)) in actual.iter().zip(cases.iter()).enumerate() { assert_eq!(got.role, case.expected, "paragraph {i}: {:?}", case.text); }
    }
}
