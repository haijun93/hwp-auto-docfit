//! Opt-in local text extraction for files explicitly added to a library.
use std::fs;
use std::path::Path;
use std::time::UNIX_EPOCH;

use crate::search::{Paragraph, SearchIndex};

pub fn index_file(index: &SearchIndex, path: &str, name: &str, box_id: i64) -> Result<(), String> {
    let p = Path::new(path);
    let ext = p.extension().and_then(|s| s.to_str()).unwrap_or("").to_ascii_lowercase();
    if !matches!(ext.as_str(), "txt" | "md" | "hwpx" | "docx" | "pptx" | "xlsx") { return Ok(()); }
    let body = extract_text(p, &ext)?;
    let metadata = fs::metadata(p).map_err(|e| e.to_string())?;
    let mtime = metadata.modified().ok().and_then(|t| t.duration_since(UNIX_EPOCH).ok()).map(|d| d.as_millis() as i64).unwrap_or(0);
    index.add_or_update(&Paragraph { path: path.to_string(), box_ids: vec![box_id.to_string()], name: name.to_string(), title: String::new(), level: 0, body, ext, mtime, page: None, sheet: None, row: None }).map_err(|e| e.to_string())
}

pub fn remove_file(index: &SearchIndex, path: &str) -> Result<(), String> {
    index.delete_path(path).map_err(|e| e.to_string())
}

pub(crate) fn extract_text(path: &Path, ext: &str) -> Result<String, String> {
    if matches!(ext, "txt" | "md") {
        return fs::read_to_string(path).or_else(|_| fs::read(path).map(|b| String::from_utf8_lossy(&b).into_owned())).map_err(|e| e.to_string());
    }
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let mut zip = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;
    let mut names = Vec::new();
    for i in 0..zip.len() {
        let name = zip.by_index(i).map_err(|e| e.to_string())?.name().map_err(|e| e.to_string())?.to_string();
        let include = match ext {
            "hwpx" => name.starts_with("Contents/section") && name.ends_with(".xml"),
            "docx" => name == "word/document.xml" || (name.starts_with("word/header") || name.starts_with("word/footer")) && name.ends_with(".xml"),
            "pptx" => name.starts_with("ppt/slides/slide") && name.ends_with(".xml"),
            "xlsx" => name.starts_with("xl/sharedStrings") && name.ends_with(".xml") || name.starts_with("xl/worksheets/sheet") && name.ends_with(".xml"),
            _ => false,
        };
        if include { names.push(name); }
    }
    names.sort();
    let mut output = String::new();
    for name in names {
        let mut entry = zip.by_name(&name).map_err(|e| e.to_string())?;
        let mut xml = String::new();
        use std::io::Read;
        entry.read_to_string(&mut xml).map_err(|e| e.to_string())?;
        output.push_str(&xml_text(&xml)); output.push('\n');
    }
    if output.trim().is_empty() { return Err("파일 본문에서 텍스트를 추출하지 못했습니다.".into()); }
    Ok(output)
}

/// 노트북 출처 문단 하나: 위계 수준(0=본문)과 표 행 여부. 표는 행 하나를 칸 사이 탭으로 이은 문단으로 낸다.
#[derive(Clone, Debug, PartialEq)]
pub struct Block { pub level: i64, pub table: bool, pub text: String }

/// 노트북 출처용 구조 추출. hwpx·docx는 개요 수준과 표 행을 살리고, 나머지는 줄 단위로 나눈다.
/// 명시 수준이 없는 본문 문단은 공문서 기호(Ⅰ. 1. □ ○ - *)로 수준을 붙인다.
pub(crate) fn extract_blocks(path: &Path, ext: &str) -> Result<Vec<Block>, String> {
    let mut blocks = match ext {
        "hwpx" => {
            let header = read_entries(path, |n| n == "Contents/header.xml")?;
            let sections = read_entries(path, |n| n.starts_with("Contents/section") && n.ends_with(".xml"))?;
            let levels = header.first().map(|(_, xml)| hwpx_outline_levels(xml)).unwrap_or_default();
            let mut out = Vec::new();
            for (_, xml) in &sections { out.extend(structured_blocks(xml, &|attrs| attr(attrs, "paraPrIDRef").and_then(|id| levels.get(id).copied()), &|_, _| None)); }
            out
        }
        "docx" => {
            let styles = read_entries(path, |n| n == "word/styles.xml")?;
            let document = read_entries(path, |n| n == "word/document.xml")?;
            let levels = styles.first().map(|(_, xml)| docx_style_levels(xml)).unwrap_or_default();
            let mut out = Vec::new();
            for (_, xml) in &document {
                out.extend(structured_blocks(xml, &|_| None, &|name, attrs| match name {
                    "pStyle" => attr(attrs, "val").and_then(|id| levels.get(id).copied()),
                    "outlineLvl" => attr(attrs, "val").and_then(|v| v.parse::<i64>().ok()).filter(|v| (0..9).contains(v)).map(|v| v + 1),
                    _ => None,
                }));
            }
            out
        }
        _ => extract_text(path, ext)?.lines().map(str::trim).filter(|l| !l.is_empty()).map(|l| {
            let hashes = if ext == "md" { l.chars().take_while(|c| *c == '#').count() } else { 0 };
            if (1..=6).contains(&hashes) && l[hashes..].starts_with(' ') { Block { level: hashes as i64, table: false, text: l[hashes..].trim().to_string() } }
            else { Block { level: 0, table: false, text: l.to_string() } }
        }).collect(),
    };
    for b in blocks.iter_mut() { if b.level == 0 && !b.table { b.level = marker_level(&b.text); } }
    if blocks.is_empty() { return Err("파일 본문에서 텍스트를 추출하지 못했습니다.".into()); }
    Ok(blocks)
}

/// 공문서 항목 기호로 수준을 정한다(없으면 0).
pub(crate) fn marker_level(text: &str) -> i64 {
    let t = text.trim_start();
    let mut chars = t.chars();
    let Some(first) = chars.next() else { return 0 };
    let spaced = |rest: &str| rest.starts_with(char::is_whitespace);
    match first {
        'Ⅰ'..='Ⅻ' => 1,
        '□' | '■' => 3,
        '○' | 'ㅇ' | '◦' | '●' if spaced(chars.as_str()) || first != 'ㅇ' => 4,
        '-' | '−' | '－' | '–' | '·' if spaced(chars.as_str()) => 5,
        '*' | '※' => 6,
        '0'..='9' => {
            let digits = t.chars().take_while(char::is_ascii_digit).count();
            let rest = &t[digits..];
            if digits <= 2 && rest.starts_with('.') && spaced(&rest[1..]) { 2 } else { 0 }
        }
        _ => 0,
    }
}

/// zip 안에서 조건에 맞는 XML을 이름의 숫자 순서(section2 < section10)로 읽는다.
fn read_entries(path: &Path, want: impl Fn(&str) -> bool) -> Result<Vec<(String, String)>, String> {
    use std::io::Read;
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let mut zip = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for i in 0..zip.len() {
        let mut entry = zip.by_index(i).map_err(|e| e.to_string())?;
        let name = entry.name().map_err(|e| e.to_string())?.to_string();
        if !want(&name) { continue; }
        let mut xml = String::new();
        entry.read_to_string(&mut xml).map_err(|e| e.to_string())?;
        out.push((name, xml));
    }
    let key = |n: &str| n.chars().filter(char::is_ascii_digit).collect::<String>().parse::<u64>().unwrap_or(0);
    out.sort_by(|a, b| key(&a.0).cmp(&key(&b.0)).then_with(|| a.0.cmp(&b.0)));
    Ok(out)
}

enum Ev<'a> { Start(&'a str, &'a str, bool), End(&'a str), Text(&'a str) }

/// 의존성 없는 얕은 XML 훑기: 이름은 접두사를 뗀 지역 이름으로 준다.
fn scan<'a>(xml: &'a str, mut f: impl FnMut(Ev<'a>)) {
    let bytes = xml.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let Some(lt) = xml[i..].find('<').map(|p| p + i) else { f(Ev::Text(&xml[i..])); break };
        if lt > i { f(Ev::Text(&xml[i..lt])); }
        let rest = &xml[lt..];
        if let Some(body) = rest.strip_prefix("<![CDATA[") {
            let end = body.find("]]>").unwrap_or(body.len());
            f(Ev::Text(&body[..end]));
            i = lt + 9 + end + 3;
            continue;
        }
        if rest.starts_with("<!--") { i = rest.find("-->").map(|p| lt + p + 3).unwrap_or(bytes.len()); continue; }
        // 따옴표 안의 '>'는 태그 끝이 아니다.
        let mut quote = 0u8; let mut j = lt + 1;
        while j < bytes.len() { let c = bytes[j]; if quote != 0 { if c == quote { quote = 0; } } else if c == b'"' || c == b'\'' { quote = c; } else if c == b'>' { break; } j += 1; }
        let tag = &xml[lt + 1..j.min(bytes.len())];
        i = j + 1;
        if tag.starts_with('?') || tag.starts_with('!') { continue; }
        let local = |n: &'a str| n.rsplit(':').next().unwrap_or(n);
        if let Some(name) = tag.strip_prefix('/') { f(Ev::End(local(name.trim()))); continue; }
        let empty = tag.ends_with('/');
        let tag = tag.trim_end_matches('/');
        let split = tag.find(char::is_whitespace).unwrap_or(tag.len());
        f(Ev::Start(local(&tag[..split]), &tag[split..], empty));
    }
}

/// 속성 값(접두사 무시). 예: attr(r#" w:val="1""#, "val") == Some("1").
fn attr<'a>(attrs: &'a str, name: &str) -> Option<&'a str> {
    let mut rest = attrs;
    while let Some(eq) = rest.find('=') {
        let key = rest[..eq].trim();
        let key = key.rsplit(':').next().unwrap_or(key);
        let after = rest[eq + 1..].trim_start();
        let q = after.chars().next()?;
        if q != '"' && q != '\'' { return None; }
        let end = after[1..].find(q)? + 1;
        if key == name { return Some(&after[1..end]); }
        rest = &after[end + 1..];
    }
    None
}

fn unescape(text: &str) -> String {
    if !text.contains('&') { return text.to_string(); }
    let mut out = String::new(); let mut rest = text;
    while let Some(p) = rest.find('&') {
        out.push_str(&rest[..p]); rest = &rest[p..];
        let Some(end) = rest.find(';').filter(|e| *e <= 12) else { out.push('&'); rest = &rest[1..]; continue };
        let name = &rest[1..end];
        let ch = match name {
            "amp" => Some('&'), "lt" => Some('<'), "gt" => Some('>'), "quot" => Some('"'), "apos" => Some('\''),
            _ if name.starts_with("#x") || name.starts_with("#X") => u32::from_str_radix(&name[2..], 16).ok().and_then(char::from_u32),
            _ if name.starts_with('#') => name[1..].parse().ok().and_then(char::from_u32),
            _ => None,
        };
        out.push(ch.unwrap_or(' ')); rest = &rest[end + 1..];
    }
    out.push_str(rest); out
}

/// hwpx header.xml: 문단 모양 id → 개요 수준(heading type="OUTLINE" level은 0부터).
fn hwpx_outline_levels(xml: &str) -> std::collections::HashMap<String, i64> {
    let mut map = std::collections::HashMap::new(); let mut current: Option<&str> = None;
    scan(xml, |ev| match ev {
        Ev::Start("paraPr", attrs, _) => current = attr(attrs, "id"),
        Ev::Start("heading", attrs, _) => if let (Some(id), Some("OUTLINE"), Some(level)) = (current, attr(attrs, "type"), attr(attrs, "level").and_then(|v| v.parse::<i64>().ok())) {
            if (0..10).contains(&level) { map.insert(id.to_string(), level + 1); }
        },
        Ev::End("paraPr") => current = None,
        _ => {}
    });
    map
}

/// docx styles.xml: 스타일 id → 수준(Title 1, heading N은 N, outlineLvl k는 k+1).
fn docx_style_levels(xml: &str) -> std::collections::HashMap<String, i64> {
    let mut map = std::collections::HashMap::new(); let mut current: Option<String> = None;
    scan(xml, |ev| match ev {
        Ev::Start("style", attrs, _) => current = attr(attrs, "styleId").map(str::to_string),
        Ev::Start("name", attrs, _) => if let (Some(id), Some(name)) = (&current, attr(attrs, "val")) {
            let lower = name.to_ascii_lowercase();
            let level = if lower == "title" { Some(1) } else { lower.strip_prefix("heading ").and_then(|n| n.trim().parse::<i64>().ok()).filter(|n| (1..10).contains(n)) };
            if let Some(level) = level { map.insert(id.clone(), level); }
        },
        Ev::Start("outlineLvl", attrs, _) => if let (Some(id), Some(v)) = (&current, attr(attrs, "val").and_then(|v| v.parse::<i64>().ok())) {
            if (0..9).contains(&v) { map.entry(id.clone()).or_insert(v + 1); }
        },
        Ev::End("style") => current = None,
        _ => {}
    });
    map
}

/// hwpx 구역·docx 본문 공통 문단·표 훑기(p·t·tbl·tr·tc는 두 형식 모두 같은 지역 이름).
/// `para_level`은 문단 시작 태그 속성으로, `prop_level`은 문단 안 속성 태그(pStyle 등)로 수준을 정한다.
fn structured_blocks(xml: &str, para_level: &dyn Fn(&str) -> Option<i64>, prop_level: &dyn Fn(&str, &str) -> Option<i64>) -> Vec<Block> {
    let mut out = Vec::new();
    let mut stack: Vec<(i64, String)> = Vec::new();
    let mut in_text = 0usize; let mut table_depth = 0usize;
    let mut row: Vec<String> = Vec::new(); let mut cell = String::new(); let mut rows: Vec<String> = Vec::new();
    scan(xml, |ev| match ev {
        Ev::Start("p", attrs, false) => stack.push((para_level(attrs).unwrap_or(0), String::new())),
        Ev::End("p") => if let Some((level, text)) = stack.pop() {
            let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
            if text.is_empty() {}
            else if table_depth > 0 { if !cell.is_empty() { cell.push(' '); } cell.push_str(&text); }
            else { out.push(Block { level, table: false, text }); }
        },
        Ev::Start("t", _, false) => in_text += 1,
        Ev::End("t") => in_text = in_text.saturating_sub(1),
        Ev::Start("tab" | "br" | "lineBreak", _, _) => if let Some(top) = stack.last_mut() { top.1.push(' '); },
        Ev::Text(text) => if in_text > 0 { if let Some(top) = stack.last_mut() { top.1.push_str(&unescape(text)); } },
        Ev::Start("tbl", _, false) => { table_depth += 1; if table_depth == 1 { row.clear(); rows.clear(); cell.clear(); } },
        // 한 행짜리 표는 제목 상자·요약 상자로 보고 일반 문단으로 낸다(예: "Ⅰ | 추진 배경" → "Ⅰ 추진 배경", 수준 1).
        Ev::End("tbl") => {
            if table_depth == 1 {
                if let [only] = rows.as_slice() {
                    let text = only.split('\t').filter(|c| !c.trim().is_empty()).collect::<Vec<_>>().join(" ");
                    out.push(Block { level: 0, table: false, text });
                } else {
                    out.extend(rows.drain(..).map(|text| Block { level: 0, table: true, text }));
                }
                rows.clear();
            }
            table_depth = table_depth.saturating_sub(1);
        }
        Ev::Start("tr", _, false) if table_depth == 1 => row.clear(),
        Ev::End("tc") if table_depth == 1 => { row.push(std::mem::take(&mut cell).replace('\t', " ")); },
        Ev::End("tr") if table_depth == 1 => if row.iter().any(|c| !c.trim().is_empty()) { rows.push(row.join("\t")); row.clear(); },
        Ev::Start(name, attrs, _) => if let (Some(level), Some(top)) = (prop_level(name, attrs), stack.last_mut()) { top.0 = level; },
        _ => {}
    });
    out
}

#[cfg(test)]
mod block_tests {
    use super::*;
    use std::io::Write;

    fn zip_file(name: &str, entries: &[(&str, &str)]) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!("klib-blocks-{}-{name}", std::process::id()));
        let mut zip = zip::ZipWriter::new(fs::File::create(&path).unwrap());
        let options = zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored);
        for (entry, body) in entries { zip.start_file(*entry, options).unwrap(); zip.write_all(body.as_bytes()).unwrap(); }
        zip.finish().unwrap();
        path
    }

    #[test]
    fn hwpx_outline_levels_markers_and_table_rows() {
        let header = r#"<hh:head xmlns:hh="h"><hh:paraPr id="0"/><hh:paraPr id="7"><hh:heading type="OUTLINE" idRef="0" level="0"/></hh:paraPr><hh:paraPr id="8"><hh:heading type="OUTLINE" idRef="0" level="1"/></hh:paraPr></hh:head>"#;
        let section = r#"<hs:sec xmlns:hs="s" xmlns:hp="p"><hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>Ⅰ</hp:t></hp:run></hp:p></hp:subList></hp:tc><hp:tc><hp:subList><hp:p/></hp:subList></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>개요 상자</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p><hp:p paraPrIDRef="7"><hp:run><hp:t>추진 배경</hp:t></hp:run></hp:p><hp:p paraPrIDRef="8"><hp:run><hp:t>현황 &amp; 문제</hp:t></hp:run></hp:p><hp:p paraPrIDRef="0"><hp:run><hp:t>□ 예산 현황</hp:t></hp:run></hp:p><hp:p paraPrIDRef="0"><hp:run><hp:t>본문 문장</hp:t></hp:run><hp:run><hp:tbl><hp:tr><hp:tc><hp:subList><hp:p paraPrIDRef="0"><hp:run><hp:t>구분</hp:t></hp:run></hp:p></hp:subList></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>금액</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr><hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>예산</hp:t></hp:run></hp:p></hp:subList></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>1,250만원</hp:t></hp:run></hp:p><hp:p><hp:run><hp:t>(증액)</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p></hs:sec>"#;
        let path = zip_file("a.hwpx", &[("mimetype", "application/hwp+zip"), ("Contents/header.xml", header), ("Contents/section0.xml", section)]);
        let blocks = extract_blocks(&path, "hwpx").unwrap();
        let _ = fs::remove_file(&path);
        let got: Vec<(i64, bool, &str)> = blocks.iter().map(|b| (b.level, b.table, b.text.as_str())).collect();
        assert_eq!(got, vec![(1, false, "Ⅰ 개요 상자"), (1, false, "추진 배경"), (2, false, "현황 & 문제"), (3, false, "□ 예산 현황"), (0, true, "구분\t금액"), (0, true, "예산\t1,250만원 (증액)"), (0, false, "본문 문장")]);
    }

    #[test]
    fn docx_heading_styles_outline_and_table() {
        let styles = r#"<w:styles xmlns:w="w"><w:style w:type="paragraph" w:styleId="1"><w:name w:val="heading 1"/></w:style><w:style w:styleId="Custom"><w:name w:val="내 제목"/><w:pPr><w:outlineLvl w:val="1"/></w:pPr></w:style></w:styles>"#;
        let document = r#"<w:document xmlns:w="w"><w:body><w:p><w:pPr><w:pStyle w:val="1"/></w:pPr><w:r><w:t>개요</w:t></w:r></w:p><w:p><w:pPr><w:pStyle w:val="Custom"/></w:pPr><w:r><w:t xml:space="preserve">세부 </w:t></w:r><w:r><w:t>항목</w:t></w:r></w:p><w:p><w:pPr><w:outlineLvl w:val="2"/></w:pPr><w:r><w:t>직접 수준</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>항목</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>내용</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:p><w:r><w:t>예산</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>1억</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:p><w:r><w:t>- 세부 설명</w:t></w:r></w:p><w:p><w:r><w:t>2026년 계획</w:t></w:r></w:p></w:body></w:document>"#;
        let path = zip_file("b.docx", &[("word/styles.xml", styles), ("word/document.xml", document)]);
        let blocks = extract_blocks(&path, "docx").unwrap();
        let _ = fs::remove_file(&path);
        let got: Vec<(i64, bool, &str)> = blocks.iter().map(|b| (b.level, b.table, b.text.as_str())).collect();
        assert_eq!(got, vec![(1, false, "개요"), (2, false, "세부 항목"), (3, false, "직접 수준"), (0, true, "항목\t내용"), (0, true, "예산\t1억"), (5, false, "- 세부 설명"), (0, false, "2026년 계획")]);
    }

    #[test]
    fn markers_and_markdown_headings() {
        assert_eq!(marker_level("Ⅱ. 추진 계획"), 1);
        assert_eq!(marker_level("1. 목적"), 2);
        assert_eq!(marker_level("2026. 11. 5. 시행"), 0);
        assert_eq!(marker_level("○ 세부"), 4);
        assert_eq!(marker_level("ㅇ 세부"), 4);
        assert_eq!(marker_level("ㅇㅇ구청"), 0);
        assert_eq!(marker_level("-1,000원"), 0);
        assert_eq!(marker_level("※ 참고"), 6);
        let path = std::env::temp_dir().join(format!("klib-blocks-{}-c.md", std::process::id()));
        fs::write(&path, "# 제목\n\n## 소제목\n본문\n#해시태그\n").unwrap();
        let blocks = extract_blocks(&path, "md").unwrap();
        let _ = fs::remove_file(&path);
        assert_eq!(blocks.iter().map(|b| (b.level, b.text.as_str())).collect::<Vec<_>>(), vec![(1, "제목"), (2, "소제목"), (0, "본문"), (0, "#해시태그")]);
    }
}

fn xml_text(xml: &str) -> String {
    let mut out = String::new(); let mut in_tag = false; let mut entity = String::new(); let mut in_entity = false;
    for ch in xml.chars() {
        if in_tag { if ch == '>' { in_tag = false; } continue; }
        if ch == '<' { in_tag = true; continue; }
        if in_entity {
            if ch == ';' { out.push(match entity.as_str() { "amp" => '&', "lt" => '<', "gt" => '>', "quot" => '"', "apos" => '\'', _ => ' ' }); entity.clear(); in_entity = false; }
            else if entity.len() < 12 { entity.push(ch); }
        } else if ch == '&' { in_entity = true; }
        else { out.push(ch); }
    }
    out
}
