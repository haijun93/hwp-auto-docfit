//! Tantivy paragraph index for the offline library.
//!
//! Morphology, synonyms, chosung and typo expansion are reserved in the schema;
//! this first stage implements the design's bigram fallback and query filters.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Once;

use tantivy::collector::TopDocs;
use tantivy::query::{BooleanQuery, Occur, Query, QueryParser};
use tantivy::schema::{Field, IndexRecordOption, Schema, TextFieldIndexing, TextOptions, Value};
use tantivy::snippet::SnippetGenerator;
use tantivy::tokenizer::{Token, TokenStream, Tokenizer};
use tantivy::{doc, Index, IndexReader, IndexWriter, ReloadPolicy, Score, TantivyDocument};

const TOKENIZER: &str = "ko_bigram";
static REGISTER: Once = Once::new();

#[derive(Clone)]
pub struct Paragraph {
    pub path: String,
    pub box_ids: Vec<String>,
    pub name: String,
    pub title: String,
    pub level: u8,
    pub body: String,
    pub ext: String,
    pub mtime: i64,
    pub page: Option<u64>,
    pub sheet: Option<String>,
    pub row: Option<u64>,
}

#[derive(Clone, Debug, Default)]
pub struct SearchOptions {
    pub limit: usize,
}

#[derive(Clone, Debug)]
pub struct SearchHit {
    pub path: String,
    pub name: String,
    pub title: String,
    pub score: Score,
    pub paragraph_count: usize,
    pub snippets: Vec<String>,
}

#[derive(Clone)]
struct Fields {
    doc_id: Field, path: Field, box_ids: Field, name: Field, title: Field,
    level: Field, body_ko: Field, body_bi: Field, body_jamo: Field,
    body_cho: Field, ext: Field, mtime: Field, page: Field, sheet: Field,
    row: Field, body: Field,
}

pub struct SearchIndex {
    index: Index,
    reader: IndexReader,
    fields: Fields,
    path: PathBuf,
}

#[derive(Clone)]
struct KoBigram;
struct BigramStream { tokens: Vec<Token>, cursor: usize }
impl Tokenizer for KoBigram {
    type TokenStream<'a> = BigramStream;
    fn token_stream<'a>(&self, text: &'a str) -> Self::TokenStream<'a> {
        let chars: Vec<(usize, char)> = text.char_indices().collect();
        let mut tokens = Vec::new();
        let mut run = Vec::new();
        let flush = |run: &mut Vec<(usize, char)>, tokens: &mut Vec<Token>| {
            if run.len() == 1 {
                let (offset, ch) = run[0];
                tokens.push(Token { offset_from: offset, offset_to: offset + ch.len_utf8(), text: ch.to_string(), position: 0, position_length: 1 });
            } else {
                for pair in run.windows(2) {
                    let (start, a) = pair[0]; let (end, b) = pair[1];
                    tokens.push(Token { offset_from: start, offset_to: end + b.len_utf8(), text: format!("{a}{b}"), position: 0, position_length: 1 });
                }
            }
            run.clear();
        };
        for (offset, ch) in chars {
            if ch.is_alphanumeric() { run.push((offset, ch)); } else { flush(&mut run, &mut tokens); }
        }
        flush(&mut run, &mut tokens);
        for (position, token) in tokens.iter_mut().enumerate() { token.position = position; }
        BigramStream { tokens, cursor: 0 }
    }
}
impl TokenStream for BigramStream {
    fn advance(&mut self) -> bool { if self.cursor >= self.tokens.len() { false } else { self.cursor += 1; true } }
    fn token(&self) -> &Token { &self.tokens[self.cursor - 1] }
}

fn text_options(tokenized: bool) -> TextOptions {
    let indexing = TextFieldIndexing::default().set_index_option(IndexRecordOption::WithFreqsAndPositions)
        .set_tokenizer(if tokenized { TOKENIZER } else { "default" });
    TextOptions::default().set_indexing_options(indexing).set_stored()
}
fn schema() -> (Schema, Fields) {
    let mut b = Schema::builder();
    let doc_id=b.add_text_field("doc_id", tantivy::schema::STRING | tantivy::schema::STORED);
    let path=b.add_text_field("path", tantivy::schema::STRING | tantivy::schema::STORED);
    let box_ids=b.add_text_field("box_ids", tantivy::schema::STRING | tantivy::schema::STORED);
    let name=b.add_text_field("name", text_options(true));
    let title=b.add_text_field("title", text_options(true));
    let level=b.add_u64_field("level", tantivy::schema::INDEXED | tantivy::schema::STORED);
    let body_ko=b.add_text_field("body_ko", text_options(false));
    let body_bi=b.add_text_field("body_bi", text_options(true));
    let body_jamo=b.add_text_field("body_jamo", text_options(false));
    let body_cho=b.add_text_field("body_cho", text_options(false));
    let ext=b.add_text_field("ext", tantivy::schema::STRING | tantivy::schema::STORED);
    let mtime=b.add_i64_field("mtime", tantivy::schema::INDEXED | tantivy::schema::STORED);
    let page=b.add_u64_field("page", tantivy::schema::STORED);
    let sheet=b.add_text_field("sheet", tantivy::schema::STRING | tantivy::schema::STORED);
    let row=b.add_u64_field("row", tantivy::schema::STORED);
    let body=b.add_text_field("body", tantivy::schema::STORED);
    (b.build(), Fields {doc_id,path,box_ids,name,title,level,body_ko,body_bi,body_jamo,body_cho,ext,mtime,page,sheet,row,body})
}
fn register() { REGISTER.call_once(|| { /* registered per-index below */ }); }
fn id(path: &str) -> String { format!("{:x}", md5::compute(path.to_lowercase().as_bytes())) }

impl SearchIndex {
    pub fn open_or_create(path: impl AsRef<Path>) -> tantivy::Result<Self> {
        register();
        let path=path.as_ref().to_path_buf();
        std::fs::create_dir_all(&path).map_err(|e| tantivy::TantivyError::InternalError(e.to_string()))?;
        let (schema, fields)=schema();
        let index=if path.join("meta.json").exists() { Index::open_in_dir(&path)? } else { Index::create_in_dir(&path, schema)? };
        index.tokenizers().register(TOKENIZER, KoBigram);
        let reader=index.reader_builder().reload_policy(ReloadPolicy::OnCommit).try_into()?;
        Ok(Self {index, reader, fields, path})
    }
    pub fn index_path(&self) -> &Path { &self.path }
    pub fn add_or_update(&self, p: &Paragraph) -> tantivy::Result<()> {
        let mut w=self.index.writer(50_000_000)?;
        w.delete_term(tantivy::Term::from_field_text(self.fields.path, &p.path));
        for part in p.body.split_inclusive(['\n','\r']) {
            let text=part.trim(); if text.is_empty() { continue; }
            let d=doc!(self.fields.doc_id=>id(&p.path), self.fields.path=>p.path.clone(), self.fields.name=>p.name.clone(), self.fields.title=>p.title.clone(), self.fields.level=>p.level as u64, self.fields.body_bi=>text.to_string(), self.fields.ext=>p.ext.clone(), self.fields.mtime=>p.mtime, self.fields.body=>text.to_string());
            let mut d=d;
            for box_id in &p.box_ids { d.add_text(self.fields.box_ids, box_id); }
            if let Some(page)=p.page { d.add_u64(self.fields.page,page); }
            if let Some(sheet)=&p.sheet { d.add_text(self.fields.sheet,sheet); }
            if let Some(row)=p.row { d.add_u64(self.fields.row,row); }
            w.add_document(d)?;
        }
        w.commit()?; self.reader.reload()?; Ok(())
    }
    pub fn delete_path(&self, path: &str) -> tantivy::Result<()> {
        let mut w=self.index.writer(50_000_000)?;
        w.delete_term(tantivy::Term::from_field_text(self.fields.path,path)); w.commit()?; self.reader.reload()?; Ok(())
    }
    pub fn search(&self, query: &str, options: SearchOptions) -> tantivy::Result<Vec<SearchHit>> {
        let parsed=parse_directives(query);
        let fields=[(self.fields.name,3.0),(self.fields.title,2.5),(self.fields.body_bi,1.0)];
        let mut parser=QueryParser::for_index(&self.index, fields.iter().map(|(f,_)|*f).collect());
        for (f,w) in fields { parser.set_field_boost(f,w); }
        let mut q=parser.parse_query(&parsed.text).unwrap_or_else(|_| Box::new(tantivy::query::EmptyQuery));
        let mut clauses=vec![(Occur::Must,q)];
        for filter in parsed.filters {
            if let Some((field,value))=filter.strip_prefix("ext:").map(|v|(self.fields.ext,v)) {
                clauses.push((Occur::Must, Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_text(field,value),IndexRecordOption::Basic))));
            } else if let Some((field,value))=filter.strip_prefix("path:").map(|v|(self.fields.path,v)) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RegexQuery::from_pattern(&format!(".*{}.*",regex::escape(value)),field)?)));
            } else if let Some(value)=filter.strip_prefix("after:").and_then(parse_date_epoch) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RangeQuery::new_i64_bounds(self.fields.mtime, std::ops::Bound::Excluded(value), std::ops::Bound::Unbounded))));
            } else if let Some(value)=filter.strip_prefix("before:").and_then(parse_date_epoch) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RangeQuery::new_i64_bounds(self.fields.mtime, std::ops::Bound::Unbounded, std::ops::Bound::Excluded(value)))));
            }
        }
        q=Box::new(BooleanQuery::new(clauses));
        let searcher=self.reader.searcher();
        let top=searcher.search(&q,&TopDocs::with_limit(options.limit.max(1)*10))?;
        let mut groups:HashMap<String,SearchHit>=HashMap::new();
        let mut gen=SnippetGenerator::create(&searcher,q.as_ref(),self.fields.body_bi)?;
        for (score,addr) in top {
            let d=searcher.doc::<TantivyDocument>(addr)?;
            let path=d.get_first(self.fields.path).and_then(|v|v.as_str()).unwrap_or("").to_string();
            let body=d.get_first(self.fields.body).and_then(|v|v.as_str()).unwrap_or("").to_string();
            let hit=groups.entry(path.clone()).or_insert_with(|| SearchHit {path,name:d.get_first(self.fields.name).and_then(|v|v.as_str()).unwrap_or("").into(),title:d.get_first(self.fields.title).and_then(|v|v.as_str()).unwrap_or("").into(),score,paragraph_count:0,snippets:Vec::new()});
            hit.paragraph_count+=1; if hit.snippets.len()<3 { hit.snippets.push(gen.snippet(&body).to_html()); }
            if score>hit.score {hit.score=score;}
        }
        let mut out:Vec<_>=groups.into_values().collect(); out.sort_by(|a,b|b.score.total_cmp(&a.score)); out.truncate(options.limit.max(1)); Ok(out)
    }
}

struct Parsed { text:String, filters:Vec<String> }
fn parse_date_epoch(s: &str) -> Option<i64> {
    let mut parts=s.split('-');
    let (y,m,d)=(parts.next()?.parse::<i64>().ok()?,parts.next()?.parse::<i64>().ok()?,parts.next()?.parse::<i64>().ok()?);
    if parts.next().is_some() || !(1..=12).contains(&m) || !(1..=31).contains(&d) { return None; }
    let y=y-(m<=2) as i64; let era=y.div_euclid(400); let yoe=y-era*400;
    let mp=m+if m>2 {-3} else {9}; let doy=(153*mp+2)/5+d-1; let doe=yoe*365+yoe/4-yoe/100+doy;
    Some((era*146097+doe-719468)*86_400_000)
}
fn parse_directives(input:&str)->Parsed {
    let mut text=String::new(); let mut filters=Vec::new();
    for word in input.split_whitespace() { if ["ext:","path:","after:","before:"].iter().any(|p|word.starts_with(p)) {filters.push(word.to_string())} else {if !text.is_empty(){text.push(' ')} text.push_str(word)} }
    Parsed{text,filters}
}

#[cfg(test)]
mod tests {
 use super::*;
 fn temp()->PathBuf { use std::sync::atomic::{AtomicU64,Ordering}; static N:AtomicU64=AtomicU64::new(0); let p=std::env::temp_dir().join(format!("klib-search-{}-{}",std::process::id(),N.fetch_add(1,Ordering::Relaxed))); std::fs::create_dir_all(&p).unwrap();p }
 fn paragraph(path:&str,body:&str)->Paragraph {Paragraph{path:path.into(),box_ids:vec!["box-a".into()],name:"?쒓뎅??臾몄꽌".into(),title:"寃???쒕ぉ".into(),level:2,body:body.into(),ext:"txt".into(),mtime:100,page:Some(1),sheet:None,row:None}}
 #[test] fn schema_has_reserved_fields(){let(s,_)=schema();for n in ["doc_id","path","box_ids","name","title","level","body_ko","body_bi","body_jamo","body_cho","ext","mtime","page","sheet","row","body"]{assert!(s.get_field(n).is_ok());}}
 #[test] fn bigrams_preserve_korean(){let ts=KoBigram.token_stream("?쒓뎅??);let mut v=vec![];let mut s=ts;while s.advance(){v.push(s.token().text.clone())}assert_eq!(v,["?쒓뎅","援?뼱"]);}
 #[test] fn bigram_single_char(){let mut s=KoBigram.token_stream("媛");assert!(s.advance());assert_eq!(s.token().text,"媛");}
 #[test] fn bigram_splits_punctuation(){let mut s=KoBigram.token_stream("媛???ㅻ씪");let mut v=vec![];while s.advance(){v.push(s.token().text.clone())}assert_eq!(v,["媛??,"?ㅻ씪"]);}
 #[test] fn tokenizer_utf8_offsets(){let mut s=KoBigram.token_stream("媛?섎떎");s.advance();assert_eq!(&"媛?섎떎"[s.token().offset_from..s.token().offset_to],"媛??);}
 #[test] fn directives_extract_filters(){let p=parse_directives("?쒓뎅??ext:txt path:abc");assert_eq!(p.text,"?쒓뎅??);assert_eq!(p.filters.len(),2);}
 #[test] fn directives_leave_phrase_and_negative(){let p=parse_directives("\"??湲??" -?쒖쇅");assert_eq!(p.text,"\"??湲??" -?쒖쇅");}
 #[test] fn add_and_search(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","?쒓뎅??寃??臾몃떒")).unwrap();assert_eq!(ix.search("?쒓뎅??,SearchOptions{limit:10}).unwrap().len(),1);let _=std::fs::remove_dir_all(dir);}
 #[test] fn update_replaces_same_path(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","?ㅻ옒?쒕궡??)).unwrap();ix.add_or_update(&paragraph("a.txt","?덈줈?대궡??)).unwrap();assert!(ix.search("?ㅻ옒?쒕궡??,SearchOptions{limit:10}).unwrap().is_empty());let _=std::fs::remove_dir_all(dir);}
 #[test] fn delete_removes_path(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","??젣 ???)).unwrap();ix.delete_path("a.txt").unwrap();assert!(ix.search("??젣",SearchOptions{limit:10}).unwrap().is_empty());let _=std::fs::remove_dir_all(dir);}
 #[test] fn groups_paragraphs(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","?쒓뎅??泥?臾몃떒\n?쒓뎅???섏㎏ 臾몃떒")).unwrap();let hits=ix.search("?쒓뎅??,SearchOptions{limit:10}).unwrap();assert_eq!(hits[0].paragraph_count,2);let _=std::fs::remove_dir_all(dir);}
 #[test] fn snippets_are_limited_to_three(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","?쒓뎅???섎굹\n?쒓뎅????n?쒓뎅????n?쒓뎅????)).unwrap();assert!(ix.search("?쒓뎅??,SearchOptions{limit:10}).unwrap()[0].snippets.len()<=3);let _=std::fs::remove_dir_all(dir);}
}

