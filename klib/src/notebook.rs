//! SQLite-backed notebooks, citations, paragraph search, and deterministic transforms.

use std::path::{Path, PathBuf};

use rusqlite::{params, Connection, OptionalExtension};
use tantivy::collector::TopDocs;
use tantivy::query::{BooleanQuery, Occur, Query, QueryParser};
use tantivy::schema::{IndexRecordOption, Schema, TextFieldIndexing, TextOptions, Value};
use tantivy::tokenizer::{Token, TokenStream, Tokenizer};
use tantivy::{doc, Index, IndexReader, ReloadPolicy, TantivyDocument};

#[derive(Clone, Debug)]
pub struct Source { pub id:i64, pub notebook_id:i64, pub kind:String, pub origin:String, pub display_name:String, pub status:String, pub reason:String, pub paragraph_count:i64, pub original_size:i64, pub original_mtime:i64 }
#[derive(Clone, Debug)]
pub struct Paragraph { pub source_id:i64, pub ordinal:i64, pub location:String, pub level:i64, pub kind:String, pub body:String }
#[derive(Clone, Debug)]
pub struct Hit { pub source_id:i64, pub ordinal:i64, pub display_name:String, pub location:String, pub score:f32, pub body:String }
#[derive(Clone, Debug)]
pub struct TransformItem { pub source_id:i64, pub ordinal:i64, pub location:String, pub level:i64, pub kind:String, pub text:String, pub score:f64 }

pub struct NotebookIndex { index:Index, reader:IndexReader, notebook:tantivy::schema::Field, source:tantivy::schema::Field, ordinal:tantivy::schema::Field, name:tantivy::schema::Field, body:tantivy::schema::Field, location:tantivy::schema::Field }

#[derive(Clone)] struct Bigram;
struct Stream { tokens:Vec<Token>, pos:usize }
impl Tokenizer for Bigram { type TokenStream<'a> = Stream; fn token_stream<'a>(&'a mut self, text:&'a str)->Stream {
    let chars:Vec<_>=text.char_indices().collect(); let mut tokens=Vec::new(); let mut run=Vec::new();
    let flush=|run:&mut Vec<(usize,char)>,tokens:&mut Vec<Token>| { if run.len()==1 { let (s,c)=run[0]; tokens.push(Token{offset_from:s,offset_to:s+c.len_utf8(),text:c.to_string(),position:0,position_length:1}); } else { for pair in run.windows(2) { let (s,a)=pair[0]; let (e,b)=pair[1]; tokens.push(Token{offset_from:s,offset_to:e+b.len_utf8(),text:format!("{a}{b}"),position:0,position_length:1}); } } run.clear(); };
    for (s,c) in chars { if c.is_alphanumeric() {run.push((s,c))} else {flush(&mut run,&mut tokens)} } flush(&mut run,&mut tokens);
    for (i,t) in tokens.iter_mut().enumerate(){t.position=i;} Stream{tokens,pos:0}
} }
impl TokenStream for Stream { fn advance(&mut self)->bool { if self.pos>=self.tokens.len(){false}else{self.pos+=1;true} } fn token(&self)->&Token{&self.tokens[self.pos-1]} fn token_mut(&mut self)->&mut Token{&mut self.tokens[self.pos-1]} }

impl NotebookIndex {
    pub fn open(path:impl AsRef<Path>)->tantivy::Result<Self>{ let path=path.as_ref(); std::fs::create_dir_all(path).map_err(|e|tantivy::TantivyError::InternalError(e.to_string()))?;
        let mut b=Schema::builder(); let notebook=b.add_u64_field("notebook",tantivy::schema::INDEXED|tantivy::schema::STORED); let source=b.add_u64_field("source",tantivy::schema::INDEXED|tantivy::schema::STORED); let ordinal=b.add_u64_field("ordinal",tantivy::schema::INDEXED|tantivy::schema::STORED);
        let text=TextOptions::default().set_indexing_options(TextFieldIndexing::default().set_index_option(IndexRecordOption::WithFreqsAndPositions).set_tokenizer("nb_bigram")).set_stored();
        let name=b.add_text_field("name",text.clone()); let body=b.add_text_field("body",text); let location=b.add_text_field("location",tantivy::schema::STRING|tantivy::schema::STORED); let schema=b.build();
        let index=if path.join("meta.json").exists(){Index::open_in_dir(path)?}else{Index::create_in_dir(path,schema)?}; index.tokenizers().register("nb_bigram",Bigram);
        let reader=index.reader_builder().reload_policy(ReloadPolicy::Manual).try_into()?; Ok(Self{index,reader,notebook,source,ordinal,name,body,location})
    }
    pub fn replace_source(&self,notebook_id:i64,source:&Source,paragraphs:&[Paragraph])->tantivy::Result<()> { let mut w=self.index.writer::<TantivyDocument>(50_000_000)?; w.delete_term(tantivy::Term::from_field_u64(self.source,source.id as u64));
        for p in paragraphs { w.add_document(doc!(self.notebook=>notebook_id as u64,self.source=>source.id as u64,self.ordinal=>p.ordinal as u64,self.name=>source.display_name.clone(),self.body=>p.body.clone(),self.location=>p.location.clone()))?; } w.commit()?; self.reader.reload()?; Ok(()) }
    pub fn remove_source(&self,source_id:i64)->tantivy::Result<()> {let mut w=self.index.writer::<TantivyDocument>(50_000_000)?;w.delete_term(tantivy::Term::from_field_u64(self.source,source_id as u64));w.commit()?;self.reader.reload()?;Ok(())}
    pub fn remove_notebook(&self,notebook_id:i64)->tantivy::Result<()> {let mut w=self.index.writer::<TantivyDocument>(50_000_000)?;w.delete_term(tantivy::Term::from_field_u64(self.notebook,notebook_id as u64));w.commit()?;self.reader.reload()?;Ok(())}
    pub fn search(&self,notebook_id:i64,query:&str,source_ids:Option<&[i64]>,limit:usize)->tantivy::Result<Vec<Hit>> { if query.trim().is_empty(){return Ok(Vec::new())} let parser=QueryParser::for_index(&self.index,vec![self.name,self.body]); let parsed=parser.parse_query(query).unwrap_or_else(|_|Box::new(tantivy::query::EmptyQuery)); let mut clauses:Vec<(Occur,Box<dyn Query>)>=vec![(Occur::Must,Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_u64(self.notebook,notebook_id as u64),IndexRecordOption::Basic))),(Occur::Must,parsed)];
        if let Some(ids)=source_ids { if ids.is_empty(){return Ok(Vec::new())} let ors=ids.iter().map(|id|(Occur::Should,Box::new(tantivy::query::TermQuery::new(tantivy::Term::from_field_u64(self.source,*id as u64),IndexRecordOption::Basic)) as Box<dyn Query>)).collect(); clauses.push((Occur::Must,Box::new(BooleanQuery::new(ors)))); }
        let q=BooleanQuery::new(clauses); let searcher=self.reader.searcher(); let docs=searcher.search(&q,&TopDocs::with_limit(limit.max(1)).order_by_score())?; let mut out=Vec::new(); for(score,addr) in docs { let d=searcher.doc::<TantivyDocument>(addr)?; out.push(Hit{source_id:d.get_first(self.source).and_then(|v|v.as_u64()).unwrap_or(0) as i64,ordinal:d.get_first(self.ordinal).and_then(|v|v.as_u64()).unwrap_or(0) as i64,display_name:d.get_first(self.name).and_then(|v|v.as_str()).unwrap_or("").into(),location:d.get_first(self.location).and_then(|v|v.as_str()).unwrap_or("").into(),score,body:d.get_first(self.body).and_then(|v|v.as_str()).unwrap_or("").into()}); } Ok(out)
    }
}

pub fn init_schema(c:&Connection)->rusqlite::Result<()> { c.execute_batch("PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS notebook(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS nb_source(id INTEGER PRIMARY KEY AUTOINCREMENT,notebook_id INTEGER NOT NULL REFERENCES notebook(id) ON DELETE CASCADE,kind TEXT NOT NULL,origin TEXT NOT NULL DEFAULT '',display_name TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',reason TEXT NOT NULL DEFAULT '',paragraph_count INTEGER NOT NULL DEFAULT 0,original_size INTEGER NOT NULL DEFAULT 0,original_mtime INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL DEFAULT 0,updated_at INTEGER NOT NULL DEFAULT 0,UNIQUE(notebook_id,id));
CREATE TABLE IF NOT EXISTS nb_paragraph(source_id INTEGER NOT NULL REFERENCES nb_source(id) ON DELETE CASCADE,ordinal INTEGER NOT NULL,location TEXT NOT NULL DEFAULT '',level INTEGER NOT NULL DEFAULT 0,kind TEXT NOT NULL DEFAULT 'text',body TEXT NOT NULL,PRIMARY KEY(source_id,ordinal),UNIQUE(source_id,ordinal));
CREATE TABLE IF NOT EXISTS nb_note(id INTEGER PRIMARY KEY AUTOINCREMENT,notebook_id INTEGER NOT NULL REFERENCES notebook(id) ON DELETE CASCADE,title TEXT NOT NULL,body TEXT NOT NULL,updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS nb_citation(id INTEGER PRIMARY KEY AUTOINCREMENT,note_id INTEGER NOT NULL REFERENCES nb_note(id) ON DELETE CASCADE,source_id INTEGER NOT NULL REFERENCES nb_source(id) ON DELETE CASCADE,paragraph_ordinal INTEGER NOT NULL,quote TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_nb_source_notebook ON nb_source(notebook_id); CREATE INDEX IF NOT EXISTS idx_nb_paragraph_source ON nb_paragraph(source_id,ordinal); CREATE INDEX IF NOT EXISTS idx_nb_note_notebook ON nb_note(notebook_id); CREATE INDEX IF NOT EXISTS idx_nb_citation_note ON nb_citation(note_id); CREATE INDEX IF NOT EXISTS idx_nb_citation_source_paragraph ON nb_citation(source_id,paragraph_ordinal);") }

fn now()->i64{std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs() as i64}
pub fn create(c:&Connection,name:&str,description:&str)->rusqlite::Result<i64>{let t=now();c.execute("INSERT INTO notebook(name,description,created_at,updated_at) VALUES(?1,?2,?3,?3)",params![name,description,t])?;Ok(c.last_insert_rowid())}
pub fn update(c:&Connection,id:i64,name:&str,description:&str)->rusqlite::Result<bool>{Ok(c.execute("UPDATE notebook SET name=?1,description=?2,updated_at=?3 WHERE id=?4",params![name,description,now(),id])?!=0)}
pub fn delete(c:&Connection,id:i64)->rusqlite::Result<bool>{Ok(c.execute("DELETE FROM notebook WHERE id=?1",[id])?!=0)}
pub fn list(c:&Connection)->rusqlite::Result<Vec<(i64,String,String,i64,i64)>>{let mut s=c.prepare("SELECT id,name,description,created_at,updated_at FROM notebook ORDER BY updated_at DESC,id DESC")?;s.query_map([],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?,r.get(4)?)))?.collect()}
pub fn add_source(c:&Connection,notebook_id:i64,kind:&str,origin:&str,name:&str)->rusqlite::Result<i64>{let t=now() as i64;c.execute("INSERT INTO nb_source(notebook_id,kind,origin,display_name,created_at,updated_at) VALUES(?1,?2,?3,?4,?5,?5)",params![notebook_id,kind,origin,name,t])?;Ok(c.last_insert_rowid())}
pub fn sources(c:&Connection,notebook_id:i64)->rusqlite::Result<Vec<Source>>{let mut s=c.prepare("SELECT id,notebook_id,kind,origin,display_name,status,reason,paragraph_count,original_size,original_mtime FROM nb_source WHERE notebook_id=?1 ORDER BY id")?;s.query_map([notebook_id],|r|Ok(Source{id:r.get(0)?,notebook_id:r.get(1)?,kind:r.get(2)?,origin:r.get(3)?,display_name:r.get(4)?,status:r.get(5)?,reason:r.get(6)?,paragraph_count:r.get(7)?,original_size:r.get(8)?,original_mtime:r.get(9)?}))?.collect()}
pub fn source_paragraphs(c:&Connection,notebook_id:i64,source_id:i64)->rusqlite::Result<Vec<Paragraph>>{let owner:Option<i64>=c.query_row("SELECT notebook_id FROM nb_source WHERE id=?1",[source_id],|r|r.get(0)).optional()?;if owner!=Some(notebook_id){return Err(rusqlite::Error::QueryReturnedNoRows)}paragraphs(c,source_id)}
pub fn remove_source(c:&Connection,id:i64)->rusqlite::Result<bool>{Ok(c.execute("DELETE FROM nb_source WHERE id=?1",[id])?!=0)}
pub fn replace_paragraphs(c:&Connection,source_id:i64,ps:&[Paragraph])->rusqlite::Result<()> {let tx=c.unchecked_transaction()?;tx.execute("DELETE FROM nb_paragraph WHERE source_id=?1",[source_id])?;{let mut s=tx.prepare("INSERT INTO nb_paragraph(source_id,ordinal,location,level,kind,body) VALUES(?1,?2,?3,?4,?5,?6)")?;for p in ps{s.execute(params![source_id,p.ordinal,p.location,p.level,p.kind,p.body])?;}}tx.execute("UPDATE nb_source SET status='ready',reason='',paragraph_count=?1,updated_at=?2 WHERE id=?3",params![ps.len() as i64,now() as i64,source_id])?;tx.commit()}
pub fn paragraphs(c:&Connection,source_id:i64)->rusqlite::Result<Vec<Paragraph>>{let mut s=c.prepare("SELECT source_id,ordinal,location,level,kind,body FROM nb_paragraph WHERE source_id=?1 ORDER BY ordinal")?;s.query_map([source_id],|r|Ok(Paragraph{source_id:r.get(0)?,ordinal:r.get(1)?,location:r.get(2)?,level:r.get(3)?,kind:r.get(4)?,body:r.get(5)?}))?.collect()}
pub fn save_note(c:&Connection,id:Option<i64>,notebook_id:i64,title:&str,body:&str)->rusqlite::Result<i64>{let t=now();if let Some(id)=id{let changed=c.execute("UPDATE nb_note SET title=?1,body=?2,updated_at=?3 WHERE id=?4 AND notebook_id=?5",params![title,body,t,id,notebook_id])?;if changed==0{return Err(rusqlite::Error::QueryReturnedNoRows)}Ok(id)}else{c.execute("INSERT INTO nb_note(notebook_id,title,body,updated_at) VALUES(?1,?2,?3,?4)",params![notebook_id,title,body,t])?;Ok(c.last_insert_rowid())}}
pub fn save_note_with_citations(c:&Connection,id:Option<i64>,notebook_id:i64,title:&str,body:&str,citations:&[(i64,i64,String)])->rusqlite::Result<i64>{let tx=c.unchecked_transaction()?;let note=save_note(&tx,id,notebook_id,title,body)?;if id.is_some(){tx.execute("DELETE FROM nb_citation WHERE note_id=?1",[note])?;}for(source,ordinal,quote)in citations{let valid:bool=tx.query_row("SELECT EXISTS(SELECT 1 FROM nb_note n JOIN nb_source s ON s.notebook_id=n.notebook_id JOIN nb_paragraph p ON p.source_id=s.id WHERE n.id=?1 AND s.id=?2 AND p.ordinal=?3)",params![note,source,ordinal],|r|r.get(0))?;if !valid{return Err(rusqlite::Error::InvalidQuery)}tx.execute("INSERT INTO nb_citation(note_id,source_id,paragraph_ordinal,quote) VALUES(?1,?2,?3,?4)",params![note,source,ordinal,quote])?;}tx.commit()?;Ok(note)}
pub fn save_citation(c:&Connection,note_id:i64,source_id:i64,ordinal:i64,quote:&str)->rusqlite::Result<i64>{
    let tx=c.unchecked_transaction()?;
    let valid:bool=tx.query_row("SELECT EXISTS(SELECT 1 FROM nb_note n JOIN nb_source s ON s.notebook_id=n.notebook_id JOIN nb_paragraph p ON p.source_id=s.id WHERE n.id=?1 AND s.id=?2 AND p.ordinal=?3)",params![note_id,source_id,ordinal],|r|r.get(0))?;
    if !valid{return Err(rusqlite::Error::InvalidQuery)}
    tx.execute("INSERT INTO nb_citation(note_id,source_id,paragraph_ordinal,quote) VALUES(?1,?2,?3,?4)",params![note_id,source_id,ordinal,quote])?;
    let id=tx.last_insert_rowid(); tx.commit()?; Ok(id)
}
pub fn citations(c:&Connection,note_id:i64)->rusqlite::Result<Vec<(i64,i64,i64,String)>>{
    let mut s=c.prepare("SELECT source_id,paragraph_ordinal,id,quote FROM nb_citation WHERE note_id=?1 ORDER BY id")?;
    s.query_map([note_id],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?)))?.collect()
}
/// 규칙 기반 변환(개요·표·숫자 문장·핵심어). 규칙 자체는 `nb_transform`에 있고, 여기서는 문단 형식만 맞춘다.
pub fn transform(items:&[Paragraph],kind:&str,limit:usize)->Result<Vec<TransformItem>,String>{
    use crate::nb_transform as nt;
    let to_para=|p:&Paragraph,text:&str|nt::Para{source_id:p.source_id.to_string(),seq:p.ordinal.max(0) as u64,page:None,level:(p.level>0).then(||p.level.min(u8::MAX as i64) as u8),text:text.to_string(),table:p.kind.eq_ignore_ascii_case("table")};
    let item=|p:&Paragraph,kind:&str,text:String,score:f64|TransformItem{source_id:p.source_id,ordinal:p.ordinal,location:p.location.clone(),level:p.level,kind:kind.to_string(),text,score};
    let find=|source:&str,seq:u64|items.iter().find(|p|p.source_id.to_string()==source&&p.ordinal.max(0) as u64==seq);
    let paras:Vec<nt::Para>=items.iter().map(|p|to_para(p,&p.body)).collect();
    let mut out=Vec::new();
    match kind{
        "outline"=>for o in nt::outline(&paras){if let Some(p)=find(&o.source_id,o.seq){out.push(item(p,&p.kind,o.text,p.level as f64))}},
        // 표 묶음마다 원문 문단을 차례로 낸다. score는 1부터 세는 표 묶음 번호.
        "tables"=>for(n,group) in nt::tables(&paras).into_iter().enumerate(){for seq in group.paragraph_seqs{if let Some(p)=find(&group.source_id,seq){out.push(item(p,"table",p.body.clone(),(n+1) as f64))}}},
        "numbers"=>{let sentences:Vec<(&Paragraph,nt::Para)>=items.iter().flat_map(|p|split_sentences(&p.body).into_iter().map(move|s|(p,s))).map(|(p,s)|(p,to_para(p,s))).collect();let only:Vec<nt::Para>=sentences.iter().map(|(_,s)|s.clone()).collect();let hits=nt::numbers(&only);let mut next=0;for hit in hits{while let Some((p,s))=sentences.get(next){next+=1;if s.source_id==hit.source_id&&s.seq==hit.seq&&s.text==hit.text{out.push(item(p,&p.kind,hit.text,1.0));break}}}},
        "keywords"=>for k in nt::keywords(&paras,limit){if let Some(p)=items.iter().find(|p|p.body.to_lowercase().contains(&k.term)){out.push(item(p,"keyword",k.term,k.count as f64))}},
        _=>return Err(format!("알 수 없는 변환 종류: {kind}"))
    }
    out.truncate(limit);Ok(out)
}
/// 문장 나누기: 마침표류 뒤가 공백·끝이고 앞이 숫자가 아닐 때만 끊는다(“2026. 11. 5.”, “3.5%”는 한 문장에 둔다). 줄바꿈은 항상 끊는다.
fn split_sentences(text:&str)->Vec<&str>{
    let mut out=Vec::new();let mut start=0;let chars:Vec<(usize,char)>=text.char_indices().collect();
    for(i,&(at,c)) in chars.iter().enumerate(){
        let end=at+c.len_utf8();
        let cut=c=='\n'||(matches!(c,'.'|'!'|'?'|'。'|'！'|'？')&&chars.get(i+1).is_none_or(|(_,n)|n.is_whitespace())&&!(c=='.'&&i>0&&chars[i-1].1.is_ascii_digit()));
        if cut{let s=text[start..end].trim();if !s.is_empty(){out.push(s)}start=end;}
    }
    let rest=text[start..].trim();if !rest.is_empty(){out.push(rest)}out
}
pub fn export_md(c:&Connection,notebook_id:i64,note_id:i64)->rusqlite::Result<Option<String>>{let note:Option<(String,String)>=c.query_row("SELECT title,body FROM nb_note WHERE id=?1 AND notebook_id=?2",params![note_id,notebook_id],|r|Ok((r.get(0)?,r.get(1)?))).optional()?;let Some((title,body))=note else{return Ok(None)};let mut out=format!("# {title}\n\n{body}");let mut s=c.prepare("SELECT c.quote,src.display_name,src.origin,c.paragraph_ordinal FROM nb_citation c JOIN nb_source src ON src.id=c.source_id WHERE c.note_id=?1 ORDER BY c.id")?;let rows=s.query_map([note_id],|r|Ok((r.get::<_,String>(0)?,r.get::<_,String>(1)?,r.get::<_,String>(2)?,r.get::<_,i64>(3)?)))?;for row in rows{let(q,n,path,o)=row?;out.push_str(&format!("\n\n> {q}\n> — {n} ({path}), 문단 {o}"));}Ok(Some(out))}

pub fn source_by_id(c:&Connection,id:i64)->rusqlite::Result<Option<Source>>{c.query_row("SELECT id,notebook_id,kind,origin,display_name,status,reason,paragraph_count,original_size,original_mtime FROM nb_source WHERE id=?1",[id],|r|Ok(Source{id:r.get(0)?,notebook_id:r.get(1)?,kind:r.get(2)?,origin:r.get(3)?,display_name:r.get(4)?,status:r.get(5)?,reason:r.get(6)?,paragraph_count:r.get(7)?,original_size:r.get(8)?,original_mtime:r.get(9)?})).optional()}
pub fn index_root(db_path:&str)->PathBuf{Path::new(db_path).parent().unwrap_or(Path::new(".")).join("notebook_tantivy")}

#[cfg(test)] mod tests { use super::*; fn db()->Connection{let c=Connection::open_in_memory().unwrap();init_schema(&c).unwrap();c} fn p(s:i64,n:i64,l:i64,k:&str,b:&str)->Paragraph{Paragraph{source_id:s,ordinal:n,location:"1".into(),level:l,kind:k.into(),body:b.into()}}
#[test]fn source_scope_and_search_order(){let dir=std::env::temp_dir().join(format!("nb-index-{}",std::process::id()));let ix=NotebookIndex::open(&dir).unwrap();let s1=Source{id:1,notebook_id:1,kind:"txt".into(),origin:"".into(),display_name:"하나".into(),status:"ready".into(),reason:"".into(),paragraph_count:2,original_size:0,original_mtime:0};let s2=Source{id:2,..s1.clone()};ix.replace_source(1,&s1,&[p(1,0,0,"text","서울 정책 자료"),p(1,1,0,"text","서울 서울 정책")]).unwrap();ix.replace_source(1,&s2,&[p(2,0,0,"text","서울 예산 정책")]).unwrap();let hits=ix.search(1,"서울 정책",None,10).unwrap();assert!(hits.len()>=2);assert!(hits[0].score>=hits[1].score);assert!(ix.search(1,"서울 정책",Some(&[2]),10).unwrap().iter().all(|h|h.source_id==2));assert!(ix.search(2,"서울 정책",None,10).unwrap().is_empty());let _=std::fs::remove_dir_all(dir);}
#[test]fn transforms_four_kinds(){let ps=vec![p(1,0,2,"text","정책 개요 2025년 예산. 다음 문장."),p(1,1,0,"table","항목 금액"),p(1,2,0,"text","정책 정책 자료")];assert_eq!(transform(&ps,"outline",10).unwrap()[0].text,"정책 개요 2025년 예산. 다음 문장.");assert_eq!(transform(&ps,"tables",10).unwrap()[0].text,"항목 금액");assert_eq!(transform(&ps,"numbers",10).unwrap()[0].text,"정책 개요 2025년 예산.");let keywords=transform(&ps,"keywords",2).unwrap();assert_eq!(keywords[0].text,"정책");assert_eq!(keywords[0].score,3.0);assert!(keywords[0].source_id>0);}
#[test]fn transforms_keep_dates_in_one_sentence_and_group_table_rows(){let ps=vec![p(1,0,0,"text","신청서는 2026. 11. 5.까지 제출합니다. 증가율은 3.5%입니다. 안내 문장."),p(1,1,0,"table","구분\t금액"),p(1,2,0,"table","예산\t1,250만원"),p(1,3,0,"text","본문"),p(1,4,0,"text","[표] 일정|담당")];let n=transform(&ps,"numbers",10).unwrap();assert_eq!(n.iter().map(|x|x.text.as_str()).collect::<Vec<_>>(),vec!["신청서는 2026. 11. 5.까지 제출합니다.","증가율은 3.5%입니다.","예산\t1,250만원"]);let t=transform(&ps,"tables",10).unwrap();assert_eq!(t.iter().map(|x|(x.ordinal,x.score)).collect::<Vec<_>>(),vec![(1,1.0),(2,1.0),(4,2.0)]);assert_eq!(t[0].text,"구분\t금액");assert!(transform(&ps,"요약",10).is_err());}
#[test]fn citation_snapshot_and_cascade(){let c=db();let n=create(&c,"노트","설명").unwrap();let s=add_source(&c,n,"txt","source.txt","원문").unwrap();replace_paragraphs(&c,s,&[p(s,0,0,"text","수정 전 원문 인용")]).unwrap();let note=save_note(&c,None,n,"제목","본문").unwrap();let quote="수정 전 원문 인용";save_citation(&c,note,s,0,quote).unwrap();replace_paragraphs(&c,s,&[p(s,0,0,"text","새 원문")]).unwrap();let saved:String=c.query_row("SELECT quote FROM nb_citation WHERE note_id=?1",[note],|r|r.get(0)).unwrap();assert_eq!(saved,quote);c.execute("UPDATE nb_source SET display_name='바뀐 원본' WHERE id=?1",[s]).unwrap();let md=export_md(&c,n,note).unwrap().unwrap();assert!(md.contains(quote));assert!(md.contains("source.txt"));assert!(export_md(&c,n+1,note).unwrap().is_none());delete(&c,n).unwrap();let count:i64=c.query_row("SELECT count(*) FROM nb_citation",[],|r|r.get(0)).unwrap();assert_eq!(count,0);}
}
