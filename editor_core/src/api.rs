//! JSON 명령 API. 요청 `{"cmd":"edit_xxx","doc":1,...}` → 응답 `{"ok":true,...}` 또는 `{"ok":false,"message":"..."}`.
//! klib 파이프 규약(`cmd`, `ok`, `message`)과 같은 모양이라 그대로 얹을 수 있다. 위치는 모두 UTF-8 바이트 오프셋.

use crate::doc::{Document, Res};
use crate::fileio::{Encoding, LineEnding};
use crate::json::{self, Json};
use crate::markdown::{self, BlockKind, BlockSet, Inline, SpanKind};
use crate::search::SearchOpts;
use std::collections::HashMap;
use std::path::Path;

pub struct Engine {
    docs: HashMap<u64, Document>,
    next: u64,
}

fn num(v: usize) -> Json {
    Json::Num(v as f64)
}
fn range_json(a: usize, b: usize) -> Vec<(&'static str, Json)> {
    vec![("start", num(a)), ("end", num(b))]
}

impl Default for Engine {
    fn default() -> Self {
        Self::new()
    }
}

impl Engine {
    pub fn new() -> Self {
        Engine { docs: HashMap::new(), next: 1 }
    }

    /// 한 줄 JSON 요청을 처리해 한 줄 JSON 응답을 돌려준다.
    pub fn handle(&mut self, request: &str) -> String {
        let resp = match json::parse(request).and_then(|req| self.exec(&req)) {
            Ok(Json::Obj(mut items)) => {
                items.insert(0, ("ok".into(), Json::Bool(true)));
                Json::Obj(items)
            }
            Ok(other) => Json::obj(vec![("ok", true.into()), ("value", other)]),
            Err(m) => Json::obj(vec![("ok", false.into()), ("message", m.into())]),
        };
        json::to_string(&resp)
    }

    fn doc(&mut self, req: &Json) -> Res<&mut Document> {
        let id = req.usize("doc").ok_or("doc(문서 번호)가 필요합니다.")? as u64;
        self.docs.get_mut(&id).ok_or_else(|| format!("문서 {id}를 찾을 수 없습니다."))
    }

    fn exec(&mut self, req: &Json) -> Res<Json> {
        let cmd = req.str("cmd").ok_or("cmd가 필요합니다.")?;
        let need = |k: &str| req.usize(k).ok_or_else(|| format!("{k}(정수)가 필요합니다."));
        let opts = SearchOpts { case_sensitive: req.bool("case_sensitive").unwrap_or(false), whole_word: req.bool("whole_word").unwrap_or(false) };
        match cmd {
            "edit_ping" => Ok(Json::obj(vec![("message", "pong".into()), ("version", env!("CARGO_PKG_VERSION").into())])),
            "edit_open" => {
                let mut d = if let Some(p) = req.str("path") {
                    Document::open(Path::new(p))?
                } else {
                    Document::from_text(req.str("text").unwrap_or(""))
                };
                if let Some(n) = req.str("line_ending") {
                    d.line_ending = LineEnding::from_name(n).ok_or("line_ending은 LF·CRLF·CR 중 하나여야 합니다.")?;
                }
                let id = self.next;
                self.next += 1;
                let info = info(&mut d);
                self.docs.insert(id, d);
                let Json::Obj(mut items) = info else { unreachable!() };
                items.insert(0, ("doc".into(), id.into()));
                Ok(Json::Obj(items))
            }
            "edit_close" => {
                let id = need("doc")? as u64;
                self.docs.remove(&id).map(|_| Json::obj(vec![])).ok_or_else(|| format!("문서 {id}를 찾을 수 없습니다."))
            }
            "edit_info" => Ok(info(self.doc(req)?)),
            "edit_text" => {
                let d = self.doc(req)?;
                let (s, e) = (req.usize("start").unwrap_or(0), req.usize("end").unwrap_or(d.len()));
                Ok(Json::obj(vec![("text", d.slice(s, e)?.into())]))
            }
            "edit_lines" => {
                let d = self.doc(req)?;
                let from = req.usize("from").unwrap_or(0);
                let to = req.usize("to").unwrap_or(d.line_count()).min(d.line_count());
                let v = (from.min(to)..to).map(|l| Json::obj(vec![("line", num(l)), ("start", num(d.line_start(l))), ("text", d.line_text(l).into())])).collect();
                Ok(Json::obj(vec![("lines", Json::Arr(v))]))
            }
            "edit_replace" => {
                let (s, e) = (need("start")?, need("end")?);
                let t = req.str("text").unwrap_or("");
                let d = self.doc(req)?;
                let c = d.replace_range(s, e, t)?;
                Ok(edited(d, c))
            }
            "edit_insert" => {
                let p = need("pos")?;
                let t = req.str("text").ok_or("text가 필요합니다.")?;
                let d = self.doc(req)?;
                let c = d.insert(p, t)?;
                Ok(edited(d, c))
            }
            "edit_delete" => {
                let (s, e) = (need("start")?, need("end")?);
                let d = self.doc(req)?;
                let c = d.delete(s, e)?;
                Ok(edited(d, c))
            }
            "edit_begin_group" => {
                self.doc(req)?.begin_group();
                Ok(Json::obj(vec![]))
            }
            "edit_end_group" => {
                let d = self.doc(req)?;
                d.end_group();
                Ok(edited(d, req.usize("cursor").unwrap_or(0)))
            }
            "edit_commit" => {
                self.doc(req)?.commit();
                Ok(Json::obj(vec![]))
            }
            "edit_undo" | "edit_redo" => {
                let d = self.doc(req)?;
                let c = if cmd == "edit_undo" { d.undo() } else { d.redo() };
                let mut j = edited(d, c.unwrap_or(0));
                if let Json::Obj(items) = &mut j {
                    items.push(("changed".into(), c.is_some().into()));
                }
                Ok(j)
            }
            "edit_line_col" => {
                let p = need("pos")?;
                let (l, c) = self.doc(req)?.line_col(p)?;
                Ok(Json::obj(vec![("line", num(l)), ("col", num(c))]))
            }
            "edit_offset" => {
                let (l, c) = (need("line")?, need("col")?);
                Ok(Json::obj(vec![("pos", num(self.doc(req)?.offset_of(l, c)))]))
            }
            "edit_to_utf16" => {
                let p = need("pos")?;
                Ok(Json::obj(vec![("unit", num(self.doc(req)?.byte_to_utf16(p)?))]))
            }
            "edit_from_utf16" => {
                let u = need("unit")?;
                Ok(Json::obj(vec![("pos", num(self.doc(req)?.utf16_to_byte(u)?))]))
            }
            "edit_find" => {
                let q = req.str("query").ok_or("query가 필요합니다.")?;
                let from = req.usize("from").unwrap_or(0);
                let wrap = req.bool("wrap").unwrap_or(true);
                let r = self.doc(req)?.find_next(q, from, opts, wrap);
                Ok(match r {
                    Some((s, e)) => Json::obj(vec![("found", true.into()), ("start", num(s)), ("end", num(e))]),
                    None => Json::obj(vec![("found", false.into())]),
                })
            }
            "edit_find_all" => {
                let q = req.str("query").ok_or("query가 필요합니다.")?;
                let limit = req.usize("limit").unwrap_or(10000);
                let v = self.doc(req)?.find_all(q, opts, limit);
                let arr = v.iter().map(|&(s, e)| Json::obj(range_json(s, e))).collect();
                Ok(Json::obj(vec![("count", num(v.len())), ("matches", Json::Arr(arr))]))
            }
            "edit_replace_next" => {
                let q = req.str("query").ok_or("query가 필요합니다.")?;
                let w = req.str("with").unwrap_or("");
                let from = req.usize("from").unwrap_or(0);
                let wrap = req.bool("wrap").unwrap_or(true);
                let d = self.doc(req)?;
                Ok(match d.replace_next(q, w, from, opts, wrap)? {
                    Some((s, e)) => {
                        let mut j = edited(d, e);
                        if let Json::Obj(items) = &mut j {
                            items.push(("replaced".into(), true.into()));
                            items.push(("start".into(), num(s)));
                        }
                        j
                    }
                    None => Json::obj(vec![("replaced", false.into())]),
                })
            }
            "edit_replace_all" => {
                let q = req.str("query").ok_or("query가 필요합니다.")?;
                let w = req.str("with").unwrap_or("");
                let d = self.doc(req)?;
                let n = d.replace_all(q, w, opts)?;
                let mut j = edited(d, 0);
                if let Json::Obj(items) = &mut j {
                    items.push(("count".into(), num(n)));
                }
                Ok(j)
            }
            "edit_md_parse" => {
                let d = self.doc(req)?;
                let from = req.usize("from_line").unwrap_or(0);
                let to = req.usize("to_line").unwrap_or(d.line_count());
                let blocks = markdown::parse(d, from, to);
                Ok(Json::obj(vec![("blocks", Json::Arr(blocks.iter().map(block_json).collect()))]))
            }
            "edit_md_inline" => {
                let (s, e) = (need("start")?, need("end")?);
                let k = match req.str("kind") {
                    Some("bold") => Inline::Bold,
                    Some("italic") => Inline::Italic,
                    Some("code") => Inline::Code,
                    _ => return Err("kind는 bold·italic·code 중 하나여야 합니다.".into()),
                };
                let d = self.doc(req)?;
                let (a, b) = markdown::toggle_inline(d, s, e, k)?;
                Ok(with_sel(edited(d, b), a, b))
            }
            "edit_md_block" => {
                let (s, e) = (need("start")?, need("end")?);
                let want = match req.str("kind") {
                    Some("paragraph") => BlockSet::Paragraph,
                    Some("heading") => BlockSet::Heading(req.usize("level").unwrap_or(1).clamp(1, 6) as u8),
                    Some("bullet") => BlockSet::Bullet,
                    Some("number") => BlockSet::Number,
                    Some("quote") => BlockSet::Quote,
                    _ => return Err("kind는 paragraph·heading·bullet·number·quote 중 하나여야 합니다.".into()),
                };
                let d = self.doc(req)?;
                let (a, b) = markdown::set_block(d, s, e, want)?;
                Ok(with_sel(edited(d, b), a, b))
            }
            "edit_md_link" => {
                let (s, e) = (need("start")?, need("end")?);
                let url = req.str("url").ok_or("url이 필요합니다.")?;
                let d = self.doc(req)?;
                let (a, b) = markdown::insert_link(d, s, e, url)?;
                Ok(with_sel(edited(d, b), a, b))
            }
            "edit_md_rule" => {
                let p = need("pos")?;
                let d = self.doc(req)?;
                let c = markdown::insert_rule(d, p)?;
                Ok(edited(d, c))
            }
            "edit_md_code_block" => {
                let (s, e) = (need("start")?, need("end")?);
                let d = self.doc(req)?;
                let (a, b) = markdown::toggle_code_block(d, s, e)?;
                Ok(with_sel(edited(d, b), a, b))
            }
            "edit_md_clear" => {
                let (s, e) = (need("start")?, need("end")?);
                let d = self.doc(req)?;
                let (a, b) = markdown::clear_format(d, s, e)?;
                Ok(with_sel(edited(d, b), a, b))
            }
            "edit_set_line_ending" => {
                let n = req.str("line_ending").ok_or("line_ending이 필요합니다.")?;
                let d = self.doc(req)?;
                d.line_ending = LineEnding::from_name(n).ok_or("line_ending은 LF·CRLF·CR 중 하나여야 합니다.")?;
                Ok(info(d))
            }
            "edit_set_encoding" => {
                let n = req.str("encoding").ok_or("encoding이 필요합니다.")?;
                let d = self.doc(req)?;
                d.encoding = Encoding::from_name(n).ok_or("encoding은 UTF-8·UTF-8 BOM·UTF-16 LE·UTF-16 BE 중 하나여야 합니다.")?;
                Ok(info(d))
            }
            "edit_save" => {
                let d = self.doc(req)?;
                let p = req.str("path").map(str::to_string).or_else(|| d.path.clone()).ok_or("path가 필요합니다.")?;
                d.save(Path::new(&p))?;
                Ok(info(d))
            }
            "edit_autosave" => {
                let p = req.str("path").ok_or("path(복구 사본 경로)가 필요합니다.")?;
                let d = self.doc(req)?;
                d.autosave(Path::new(p))?;
                Ok(Json::obj(vec![("saved", true.into()), ("dirty", d.is_dirty().into())]))
            }
            other => Err(format!("알 수 없는 명령: {other}")),
        }
    }
}

fn info(d: &mut Document) -> Json {
    let st = d.stats();
    Json::obj(vec![
        ("len", num(d.len())),
        ("lines", num(st.lines)),
        ("chars", num(st.chars)),
        ("bytes", num(st.bytes)),
        ("words", num(st.words)),
        ("line_ending", d.line_ending.name().into()),
        ("mixed_line_endings", d.mixed_line_endings.into()),
        ("encoding", d.encoding.name().into()),
        ("path", d.path.clone().into()),
        ("dirty", d.is_dirty().into()),
        ("can_undo", d.can_undo().into()),
        ("can_redo", d.can_redo().into()),
    ])
}

/// 편집 결과 공통 응답: 커서, 길이, 변경 여부, 실행취소 가능 여부.
fn edited(d: &mut Document, cursor: usize) -> Json {
    Json::obj(vec![
        ("cursor", num(cursor)),
        ("len", num(d.len())),
        ("chars", num(d.buf.char_count())),
        ("lines", num(d.line_count())),
        ("dirty", d.is_dirty().into()),
        ("can_undo", d.can_undo().into()),
        ("can_redo", d.can_redo().into()),
    ])
}

fn with_sel(mut j: Json, a: usize, b: usize) -> Json {
    if let Json::Obj(items) = &mut j {
        items.push(("sel_start".into(), num(a)));
        items.push(("sel_end".into(), num(b)));
    }
    j
}

fn block_json(b: &markdown::Block) -> Json {
    let (kind, extra): (&str, Vec<(&str, Json)>) = match &b.kind {
        BlockKind::Blank => ("blank", vec![]),
        BlockKind::Paragraph => ("paragraph", vec![]),
        BlockKind::Heading(l) => ("heading", vec![("level", num(*l as usize))]),
        BlockKind::Bullet { indent } => ("bullet", vec![("indent", num(*indent))]),
        BlockKind::Number { n, indent } => ("number", vec![("n", (*n).into()), ("indent", num(*indent))]),
        BlockKind::Quote => ("quote", vec![]),
        BlockKind::Rule => ("rule", vec![]),
        BlockKind::Fence { lang, open } => ("fence", vec![("lang", lang.clone().into()), ("open", (*open).into())]),
        BlockKind::Code => ("code", vec![]),
    };
    let spans = b
        .spans
        .iter()
        .map(|s| {
            let k = match s.kind {
                SpanKind::Bold => "bold",
                SpanKind::Italic => "italic",
                SpanKind::Code => "code",
                SpanKind::Link => "link",
            };
            let mut v = vec![("kind", k.into()), ("start", num(s.start)), ("end", num(s.end)), ("content_start", num(s.content_start)), ("content_end", num(s.content_end))];
            if let Some((a, b)) = s.url {
                v.push(("url_start", num(a)));
                v.push(("url_end", num(b)));
            }
            Json::obj(v)
        })
        .collect();
    let mut v = vec![("kind", kind.into()), ("line", num(b.line)), ("start", num(b.start)), ("end", num(b.end)), ("content_start", num(b.content_start)), ("spans", Json::Arr(spans))];
    v.extend(extra);
    Json::obj(v)
}
