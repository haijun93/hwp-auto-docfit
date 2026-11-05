//! Tantivy paragraph index for the offline library.
//!
//! Morphology, synonyms, chosung and typo expansion are reserved in the schema;
//! this first stage implements the design's bigram fallback and query filters.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::SystemTime;

use tantivy::collector::TopDocs;
use tantivy::query::{BooleanQuery, Occur, Query, QueryParser};
use tantivy::schema::{Field, IndexRecordOption, Schema, TextFieldIndexing, TextOptions, Value};
use tantivy::snippet::SnippetGenerator;
use tantivy::tokenizer::{Token, TokenStream, Tokenizer};
use tantivy::{doc, Index, IndexReader, ReloadPolicy, Score, TantivyDocument};

const TOKENIZER: &str = "ko_bigram";

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
    pub page: Option<u64>,
    pub box_ids: Vec<String>,
    pub hit_pages: Vec<Option<u64>>,
    pub highlighted: Vec<String>,
}

#[derive(Clone)]
struct Fields {
    doc_id: Field, path: Field, box_ids: Field, name: Field, name_cho: Field, title: Field,
    level: Field, body_ko: Field, body_bi: Field, body_jamo: Field,
    body_cho: Field, ext: Field, mtime: Field, page: Field, sheet: Field,
    row: Field, body: Field, notebook_id: Field, source_id: Field,
    paragraph_ordinal: Field, location: Field,
}

pub struct SearchIndex {
    index: Index,
    reader: IndexReader,
    fields: Fields,
    path: PathBuf,
    synonyms: Mutex<SynonymCache>,
}

#[derive(Default)]
struct SynonymCache { modified: Option<(SystemTime, u64)>, loaded: bool, groups: Vec<Vec<String>> }

#[derive(Clone)]
struct KoBigram;
struct BigramStream { tokens: Vec<Token>, cursor: usize }
impl Tokenizer for KoBigram {
    type TokenStream<'a> = BigramStream;
    fn token_stream<'a>(&'a mut self, text: &'a str) -> Self::TokenStream<'a> {
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
    fn token_mut(&mut self) -> &mut Token { &mut self.tokens[self.cursor - 1] }
}

fn text_options(tokenizer: &str) -> TextOptions {
    let indexing = TextFieldIndexing::default().set_index_option(IndexRecordOption::WithFreqsAndPositions)
        .set_tokenizer(tokenizer);
    TextOptions::default().set_indexing_options(indexing).set_stored()
}
fn schema() -> (Schema, Fields) {
    let mut b = Schema::builder();
    let doc_id=b.add_text_field("doc_id", tantivy::schema::STRING | tantivy::schema::STORED);
    let path=b.add_text_field("path", tantivy::schema::STRING | tantivy::schema::STORED);
    let box_ids=b.add_text_field("box_ids", tantivy::schema::STRING | tantivy::schema::STORED);
    let name=b.add_text_field("name", text_options(TOKENIZER));
    let name_cho=b.add_text_field("name_cho", text_options("default"));
    let title=b.add_text_field("title", text_options(TOKENIZER));
    let level=b.add_u64_field("level", tantivy::schema::INDEXED | tantivy::schema::STORED);
    let body_ko=b.add_text_field("body_ko", text_options(TOKENIZER));
    let body_bi=b.add_text_field("body_bi", text_options(TOKENIZER));
    let body_jamo=b.add_text_field("body_jamo", text_options("default"));
    let body_cho=b.add_text_field("body_cho", text_options("default"));
    let ext=b.add_text_field("ext", tantivy::schema::STRING | tantivy::schema::STORED);
    let mtime=b.add_i64_field("mtime", tantivy::schema::INDEXED | tantivy::schema::STORED);
    let page=b.add_u64_field("page", tantivy::schema::STORED);
    let sheet=b.add_text_field("sheet", tantivy::schema::STRING | tantivy::schema::STORED);
    let row=b.add_u64_field("row", tantivy::schema::STORED);
    let body=b.add_text_field("body", tantivy::schema::STORED);
    let notebook_id=b.add_u64_field("notebook_id",tantivy::schema::INDEXED|tantivy::schema::STORED);
    let source_id=b.add_u64_field("source_id",tantivy::schema::INDEXED|tantivy::schema::STORED);
    let paragraph_ordinal=b.add_u64_field("paragraph_ordinal",tantivy::schema::INDEXED|tantivy::schema::STORED);
    let location=b.add_text_field("location",tantivy::schema::STRING|tantivy::schema::STORED);
    (b.build(), Fields {doc_id,path,box_ids,name,name_cho,title,level,body_ko,body_bi,body_jamo,body_cho,ext,mtime,page,sheet,row,body,notebook_id,source_id,paragraph_ordinal,location})
}
fn id(path: &str) -> String { format!("{:x}", md5::compute(path.to_lowercase().as_bytes())) }

impl SearchIndex {
    pub fn replace_notebook_source(&self, notebook_id:i64, source:&crate::notebook::Source, paragraphs:&[crate::notebook::Paragraph])->tantivy::Result<()> {
        let mut writer=self.index.writer::<TantivyDocument>(50_000_000)?;
        writer.delete_term(tantivy::Term::from_field_u64(self.fields.source_id,source.id as u64));
        for p in paragraphs {
            let path=format!("notebook/{notebook_id}/source/{}",source.id);
            let doc=doc!(self.fields.doc_id=>format!("{notebook_id}:{}:{}",source.id,p.ordinal),
                self.fields.path=>path,self.fields.box_ids=>format!("notebook:{notebook_id}"),
                self.fields.name=>source.display_name.clone(),self.fields.title=>source.display_name.clone(),
                self.fields.level=>p.level.max(0) as u64,self.fields.body_ko=>p.body.clone(),
                self.fields.body_bi=>p.body.clone(),self.fields.body_jamo=>jamo_text(&p.body),
                self.fields.body_cho=>cho_text(&p.body),self.fields.ext=>"nb".to_string(),
                self.fields.mtime=>source.original_mtime,self.fields.body=>p.body.clone(),
                self.fields.notebook_id=>notebook_id as u64,self.fields.source_id=>source.id as u64,
                self.fields.paragraph_ordinal=>p.ordinal as u64,self.fields.location=>p.location.clone());
            writer.add_document(doc)?;
        }
        writer.commit()?;self.reader.reload()?;Ok(())
    }
    pub fn remove_notebook_source(&self,source_id:i64)->tantivy::Result<()> {
        let mut writer=self.index.writer::<TantivyDocument>(50_000_000)?;
        writer.delete_term(tantivy::Term::from_field_u64(self.fields.source_id,source_id as u64));
        writer.commit()?;self.reader.reload()?;Ok(())
    }
    pub fn remove_notebook(&self,notebook_id:i64)->tantivy::Result<()> {
        let mut writer=self.index.writer::<TantivyDocument>(50_000_000)?;
        writer.delete_term(tantivy::Term::from_field_u64(self.fields.notebook_id,notebook_id as u64));
        writer.commit()?;self.reader.reload()?;Ok(())
    }
    pub fn search_notebook(&self,notebook_id:i64,query:&str,source_ids:Option<&[i64]>,limit:usize)->tantivy::Result<Vec<crate::notebook::Hit>> {
        if query.trim().is_empty(){return Ok(Vec::new())}
        let parser=QueryParser::for_index(&self.index,vec![self.fields.name,self.fields.body_ko,self.fields.body_bi]);
        let parsed=parser.parse_query(query).unwrap_or_else(|_|Box::new(tantivy::query::EmptyQuery));
        let mut clauses:Vec<(Occur,Box<dyn Query>)>=vec![
            (Occur::Must,Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_u64(self.fields.notebook_id,notebook_id as u64),IndexRecordOption::Basic))),
            (Occur::Must,parsed)];
        if let Some(ids)=source_ids{
            if ids.is_empty(){return Ok(Vec::new())}
            let terms=ids.iter().map(|id|(Occur::Should,Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_u64(self.fields.source_id,*id as u64),IndexRecordOption::Basic)) as Box<dyn Query>)).collect();
            clauses.push((Occur::Must,Box::new(BooleanQuery::new(terms))));
        }
        let q=BooleanQuery::new(clauses);let searcher=self.reader.searcher();
        let docs=searcher.search(&q,&TopDocs::with_limit(limit.max(1)))?;let mut hits=Vec::new();
        for(score,address) in docs{let d=searcher.doc::<TantivyDocument>(address)?;hits.push(crate::notebook::Hit{
            source_id:d.get_first(self.fields.source_id).and_then(|v|v.as_u64()).unwrap_or(0) as i64,
            ordinal:d.get_first(self.fields.paragraph_ordinal).and_then(|v|v.as_u64()).unwrap_or(0) as i64,
            display_name:d.get_first(self.fields.name).and_then(|v|v.as_str()).unwrap_or("").into(),
            location:d.get_first(self.fields.location).and_then(|v|v.as_str()).unwrap_or("").into(),
            score,body:d.get_first(self.fields.body).and_then(|v|v.as_str()).unwrap_or("").into()});}
        Ok(hits)
    }
    pub fn open_or_create(path: impl AsRef<Path>) -> tantivy::Result<Self> {
        let path=path.as_ref().to_path_buf();
        std::fs::create_dir_all(&path).map_err(|e| tantivy::TantivyError::InternalError(e.to_string()))?;
        let (schema, fields)=schema();
        let index=if path.join("meta.json").exists() { Index::open_in_dir(&path)? } else { Index::create_in_dir(&path, schema)? };
        index.tokenizers().register(TOKENIZER, KoBigram);
        #[cfg(feature = "ko-dic")]
        {
            let dict=lindera::dictionary::load_dictionary_from_kind(lindera::dictionary::DictionaryKind::KoDic)
                .map_err(|e|tantivy::TantivyError::InvalidArgument(format!("ko-dic load failed: {e}")))?;
            let segmenter=lindera::segmenter::Segmenter::new(lindera::mode::Mode::Normal,dict,None);
            index.tokenizers().register("ko_morph",lindera_tantivy::tokenizer::LinderaTokenizer::from_segmenter(segmenter));
        }
        let reader=index.reader_builder().reload_policy(ReloadPolicy::Manual).try_into()?;
        Ok(Self {index, reader, fields, path, synonyms: Mutex::new(SynonymCache::default())})
    }
    pub fn index_path(&self) -> &Path { &self.path }
    pub fn add_or_update(&self, p: &Paragraph) -> tantivy::Result<()> {
        let mut w=self.index.writer::<TantivyDocument>(50_000_000)?;
        w.delete_term(tantivy::Term::from_field_text(self.fields.path, &p.path));
        for part in p.body.split_inclusive(['\n','\r']) {
            let text=part.trim(); if text.is_empty() { continue; }
            let d=doc!(self.fields.doc_id=>id(&p.path), self.fields.path=>p.path.clone(), self.fields.name=>p.name.clone(), self.fields.title=>p.title.clone(), self.fields.level=>p.level as u64, self.fields.body_bi=>text.to_string(), self.fields.body_ko=>text.to_string(), self.fields.body_jamo=>jamo_text(text), self.fields.body_cho=>cho_text(text), self.fields.ext=>p.ext.clone(), self.fields.mtime=>p.mtime, self.fields.body=>text.to_string());
            let mut d=d;
            for box_id in &p.box_ids { d.add_text(self.fields.box_ids, box_id); }
            d.add_text(self.fields.name_cho,cho_text(&p.name));
            if let Some(page)=p.page { d.add_u64(self.fields.page,page); }
            if let Some(sheet)=&p.sheet { d.add_text(self.fields.sheet,sheet); }
            if let Some(row)=p.row { d.add_u64(self.fields.row,row); }
            w.add_document(d)?;
        }
        w.commit()?; self.reader.reload()?; Ok(())
    }
    pub fn delete_path(&self, path: &str) -> tantivy::Result<()> {
        let mut w=self.index.writer::<TantivyDocument>(50_000_000)?;
        w.delete_term(tantivy::Term::from_field_text(self.fields.path,path)); w.commit()?; self.reader.reload()?; Ok(())
    }
    pub fn search(&self, query: &str, options: SearchOptions) -> tantivy::Result<Vec<SearchHit>> {
        let parsed=parse_directives(query);
        let fields=[(self.fields.name,3.0),(self.fields.title,2.5),(self.fields.body_ko,1.0),(self.fields.body_bi,0.4)];
        let mut parser=QueryParser::for_index(&self.index, fields.iter().map(|(f,_)|*f).collect());
        for (f,w) in fields { parser.set_field_boost(f,w); }
        let groups=self.load_synonyms();
        let mut synonym_terms=Vec::new();
        for term in parsed.text.split_whitespace() {
            if let Some(group)=groups.iter().find(|g|g.iter().any(|s|s.eq_ignore_ascii_case(term))) {
                synonym_terms.extend(group.iter().filter(|s|!s.eq_ignore_ascii_case(term)).cloned());
            }
        }
        let base=parser.parse_query(&parsed.text).unwrap_or_else(|_| Box::new(tantivy::query::EmptyQuery));
        let mut query_clauses: Vec<(Occur, Box<dyn Query>)>=vec![(Occur::Should,base)];
        if !synonym_terms.is_empty() {
            let syn=parser.parse_query(&synonym_terms.join(" ")).unwrap_or_else(|_| Box::new(tantivy::query::EmptyQuery));
            query_clauses.push((Occur::Should,Box::new(tantivy::query::BoostQuery::new(syn,0.8))));
        }
        let mut q: Box<dyn Query>=Box::new(BooleanQuery::new(query_clauses));
        if is_chosung_query(&parsed.text) {
            let cho=cho_text(&parsed.text);
            let cq=Box::new(tantivy::query::RegexQuery::from_pattern(&format!("{}.*",regex::escape(&cho)),self.fields.body_cho)?);
            let nq=Box::new(tantivy::query::RegexQuery::from_pattern(&format!("{}.*",regex::escape(&cho)),self.fields.name_cho)?);
            let cho_clauses: Vec<(Occur, Box<dyn Query>)>=vec![(Occur::Should, Box::new(tantivy::query::BoostQuery::new(cq,1.0))),(Occur::Should,Box::new(tantivy::query::BoostQuery::new(nq,3.0))),(Occur::Should,q)];
            q=Box::new(BooleanQuery::new(cho_clauses));
        }
        let searcher=self.reader.searcher();
        if searcher.search(&q,&TopDocs::with_limit(options.limit.max(1)))?.len()<options.limit.max(1) {
            if let Some(fuzzy)=fuzzy_query(&parsed.text,self.fields.body_jamo) {
                q=Box::new(BooleanQuery::new(vec![(Occur::Should,q),(Occur::Should,Box::new(tantivy::query::BoostQuery::new(fuzzy,0.5)))]));
            }
        }
        let mut clauses=vec![
            (Occur::Must,q),
            (Occur::MustNot,Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_text(self.fields.ext,"nb"),IndexRecordOption::Basic)) as Box<dyn Query>),
        ];
        for filter in parsed.filters {
            if let Some((field,value))=filter.strip_prefix("ext:").map(|v|(self.fields.ext,v)) {
                clauses.push((Occur::Must, Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_text(field,value),IndexRecordOption::Basic))));
            } else if let Some((field,value))=filter.strip_prefix("path:").map(|v|(self.fields.path,v)) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RegexQuery::from_pattern(&format!(".*{}.*",regex::escape(value)),field)?)));
            } else if let Some(value)=filter.strip_prefix("after:").and_then(parse_date_epoch) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RangeQuery::new_i64_bounds("mtime".to_string(), std::ops::Bound::Excluded(value), std::ops::Bound::Unbounded))));
            } else if let Some(value)=filter.strip_prefix("before:").and_then(parse_date_epoch) {
                clauses.push((Occur::Must, Box::new(tantivy::query::RangeQuery::new_i64_bounds("mtime".to_string(), std::ops::Bound::Unbounded, std::ops::Bound::Excluded(value)))));
            }
        }
        q=Box::new(BooleanQuery::new(clauses));
        let top=searcher.search(&q,&TopDocs::with_limit(options.limit.max(1)*10))?;
        let mut groups:HashMap<String,SearchHit>=HashMap::new();
        let mut generator=SnippetGenerator::create(&searcher,q.as_ref(),self.fields.body_bi)?;
        for (score,addr) in top {
            let d=searcher.doc::<TantivyDocument>(addr)?;
            let path=d.get_first(self.fields.path).and_then(|v|v.as_str()).unwrap_or("").to_string();
            let body=d.get_first(self.fields.body).and_then(|v|v.as_str()).unwrap_or("").to_string();
            let page=d.get_first(self.fields.page).and_then(|v|v.as_u64());
            let hit=groups.entry(path.clone()).or_insert_with(|| SearchHit {path,name:d.get_first(self.fields.name).and_then(|v|v.as_str()).unwrap_or("").into(),title:d.get_first(self.fields.title).and_then(|v|v.as_str()).unwrap_or("").into(),score,paragraph_count:0,snippets:Vec::new(),page,box_ids:d.get_all(self.fields.box_ids).filter_map(|v|v.as_str().map(str::to_string)).collect(),hit_pages:Vec::new(),highlighted:Vec::new()});
            hit.paragraph_count+=1;
            if hit.snippets.len()<3 {
                let snippet=generator.snippet(&body);
                hit.highlighted.extend(snippet.highlighted().iter().map(|range| snippet.fragment()[range.clone()].to_string()));
                hit.snippets.push(snippet.fragment().to_string());
            }
            hit.hit_pages.push(page);
            if score>hit.score {hit.score=score;}
        }
        let mut out:Vec<_>=groups.into_values().collect(); out.sort_by(|a,b|b.score.total_cmp(&a.score)); out.truncate(options.limit.max(1)); Ok(out)
    }

    fn load_synonyms(&self) -> Vec<Vec<String>> {
        let executable_data=std::env::current_exe().ok().and_then(|p|p.parent().map(|d|d.join("data/synonyms.tsv")));
        let candidates=[executable_data.unwrap_or_default(),self.path.join("data/synonyms.tsv"), self.path.join("synonyms.tsv"), self.path.parent().unwrap_or(&self.path).join("data/synonyms.tsv")];
        let file=candidates.iter().find(|p|p.exists()).cloned().unwrap_or_else(||self.path.join("data/synonyms.tsv"));
        let modified=std::fs::metadata(&file).ok().and_then(|m|m.modified().ok().map(|t|(t,m.len())));
        let mut cache=self.synonyms.lock().unwrap_or_else(|e|e.into_inner());
        if !cache.loaded || modified!=cache.modified {
            let contents=std::fs::read_to_string(&file).unwrap_or_else(|_|include_str!("../data/synonyms.tsv").to_string());
            let mut groups=contents.lines().filter_map(|line| {let row:Vec<String>=line.trim_start_matches('\u{feff}').split('\t').map(str::trim).filter(|x|!x.is_empty()&&!x.starts_with('#')).map(str::to_string).collect();(row.len()>1).then_some(row)}).collect::<Vec<_>>();
            if groups.is_empty() { groups=vec![vec!["동주민센터".into(),"행정복지센터".into()],vec!["TF".into(),"전담팀".into()],vec!["주민센터".into(),"행정센터".into()]]; }
            cache.modified=modified; cache.loaded=true; cache.groups=groups;
        }
        cache.groups.clone()
    }
}

fn cho_char(c: char) -> char {
    const CHO: [char;19]=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
    let n=c as u32;
    if (0xAC00..=0xD7A3).contains(&n) { CHO[((n-0xAC00)/588) as usize] } else { c }
}
fn cho_text(s:&str)->String { s.chars().map(cho_char).collect() }
fn is_chosung_query(s:&str)->bool { !s.is_empty() && s.chars().all(|c| matches!(c,'ㄱ'..='ㅎ'|'ㄲ'|'ㄸ'|'ㅃ'|'ㅆ'|'ㅉ')) }
fn jamo_char(c:char)->String {
    const C:[char;19]=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
    const V:[char;21]=['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ'];
    const T:[char;28]=[' ','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
    let n=c as u32;
    if (0xAC00..=0xD7A3).contains(&n) { let x=n-0xAC00; format!("{}{}{}",C[(x/588) as usize],V[((x%588)/28) as usize],T[(x%28) as usize]).replace(" ","") } else { c.to_string() }
}
fn jamo_text(s:&str)->String { s.chars().map(jamo_char).collect::<String>().to_lowercase() }
fn fuzzy_query(query:&str, field:Field)->Option<Box<dyn Query>> {
    let terms:Vec<String>=query.split_whitespace().map(|s|jamo_text(s).replace(" ","")).filter(|s|s.chars().count()>4).collect();
    let mut clauses=Vec::new();
    for term in terms { clauses.push((Occur::Should,Box::new(tantivy::query::FuzzyTermQuery::new(tantivy::Term::from_field_text(field,&term),1,true)) as Box<dyn Query>)); }
    if clauses.is_empty(){None}else{Some(Box::new(BooleanQuery::new(clauses)))}
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
 fn paragraph(path:&str,body:&str)->Paragraph {Paragraph{path:path.into(),box_ids:vec!["box-a".into()],name:"\u{d55c}\u{ad6d}\u{c5b4} \u{bb38}\u{c11c}".into(),title:"\u{ac80}\u{c0c9} \u{c81c}\u{baa9}".into(),level:2,body:body.into(),ext:"txt".into(),mtime:100,page:Some(1),sheet:None,row:None}}
 #[test] fn schema_has_reserved_fields(){let(s,_)=schema();for n in ["doc_id","path","box_ids","name","name_cho","title","level","body_ko","body_bi","body_jamo","body_cho","ext","mtime","page","sheet","row","body"]{assert!(s.get_field(n).is_ok());}}
 #[test] fn bigrams_preserve_korean(){let mut s=KoBigram.token_stream("\u{d55c}\u{ad6d}\u{c5b4} \u{bb38}\u{c11c}");let mut v=vec![];while s.advance(){v.push(s.token().text.clone())}assert_eq!(v,["\u{d55c}\u{ad6d}","\u{ad6d}\u{c5b4}","\u{bb38}\u{c11c}"]);}
 #[test] fn bigram_single_char(){let mut s=KoBigram.token_stream("\u{ac00}");assert!(s.advance());assert_eq!(s.token().text,"\u{ac00}");}
 #[test] fn bigram_splits_punctuation(){let mut s=KoBigram.token_stream("\u{ac00}\u{b098},\u{b2e4}\u{b77c}");let mut v=vec![];while s.advance(){v.push(s.token().text.clone())}assert_eq!(v,["\u{ac00}\u{b098}","\u{b2e4}\u{b77c}"]);}
 #[test] fn tokenizer_utf8_offsets(){let mut s=KoBigram.token_stream("\u{ac00}\u{b098}\u{b2e4}");s.advance();assert_eq!(&"\u{ac00}\u{b098}\u{b2e4}"[s.token().offset_from..s.token().offset_to],"\u{ac00}\u{b098}");}
 #[test] fn directives_extract_filters(){let p=parse_directives("\u{d55c}\u{ad6d}\u{c5b4} ext:txt path:abc");assert_eq!(p.text,"\u{d55c}\u{ad6d}\u{c5b4}");assert_eq!(p.filters.len(),2);}
 #[test] fn add_and_search(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();ix.add_or_update(&paragraph("a.txt","\u{d55c}\u{ad6d}\u{c5b4} \u{ac80}\u{c0c9} \u{bb38}\u{b2e8}")).unwrap();assert_eq!(ix.search("\u{d55c}\u{ad6d}\u{c5b4}",SearchOptions{limit:10}).unwrap().len(),1);let _=std::fs::remove_dir_all(dir);}
 #[test] fn notebook_index_reuses_search_index_with_exact_scope_and_rank(){let dir=temp();let ix=SearchIndex::open_or_create(&dir).unwrap();let source=|id|crate::notebook::Source{id,notebook_id:7,kind:"txt".into(),origin:"".into(),display_name:format!("자료{id}"),status:"ready".into(),reason:"".into(),paragraph_count:1,original_size:0,original_mtime:0};let a=source(31);let b=source(32);ix.replace_notebook_source(7,&a,&[crate::notebook::Paragraph{source_id:31,ordinal:0,location:"1".into(),level:0,kind:"text".into(),body:"서울 예산".into()}]).unwrap();ix.replace_notebook_source(7,&b,&[crate::notebook::Paragraph{source_id:32,ordinal:0,location:"2".into(),level:0,kind:"text".into(),body:"서울 서울 예산 예산".into()}]).unwrap();let all=ix.search_notebook(7,"서울 예산",None,10).unwrap();assert_eq!(all.len(),2);assert!(all[0].score>=all[1].score);assert!(ix.search_notebook(7,"서울 예산",Some(&[31]),10).unwrap().iter().all(|h|h.source_id==31));assert!(ix.search_notebook(8,"서울 예산",None,10).unwrap().is_empty());ix.remove_notebook(7).unwrap();assert!(ix.search_notebook(7,"서울",None,10).unwrap().is_empty());let _=std::fs::remove_dir_all(dir);}
 #[test] fn chosung_and_fuzzy_helpers(){assert_eq!(cho_text("\u{d589}\u{c815}\u{bcf5}\u{c9c0}\u{c13c}\u{d130}"),"\u{314E}\u{3148}\u{3142}\u{3148}\u{3145}\u{314C}");assert!(is_chosung_query("\u{314E}\u{3148}\u{3142}\u{3148}"));assert!(fuzzy_query("\u{d589}\u{c815}\u{bcf5}\u{c9c0}\u{c13c}\u{d130}",schema().1.body_jamo).is_some());}
}
