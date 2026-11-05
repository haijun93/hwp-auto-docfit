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
