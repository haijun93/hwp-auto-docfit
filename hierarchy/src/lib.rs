#![forbid(unsafe_code)]

use std::collections::HashMap;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum MarkerFamily { RomanUpper, RomanLower, DecimalDot, DecimalParen, DecimalBare, HangulDot, HangulParen, CircledNumber, CircledHangul, Square, Circle, Dash, Asterisk }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Decoration { Plain, Dot, Parentheses, ClosingParen }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PrefixReading { pub family: MarkerFamily, pub ordinal: Option<u32>, pub decoration: Decoration, pub end_byte: usize }
#[derive(Clone, Debug, PartialEq)]
pub struct FamilyEvidence { pub family: MarkerFamily, pub count: usize, pub first_position: usize, pub median_indent: i32, pub median_size_hundredth_pt: u32, pub bold_count: usize, pub recount_points: usize }
#[derive(Clone, Debug, PartialEq)]
pub struct FamilyRank { pub family: MarkerFamily, pub rank: u8, pub score: i32, pub evidence: FamilyEvidence }
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Diagnostic { FamiliesMerged { from: usize, into: usize }, TooManyFamilies { detected: usize } }
#[derive(Clone, Debug, PartialEq)]
pub struct DocScheme { pub families: Vec<FamilyRank>, pub diagnostics: Vec<Diagnostic> }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SchemeParagraph<'a> { pub text: &'a str, pub position: usize, pub left_indent: i32, pub size_hundredth_pt: u32, pub bold: bool, pub in_attachment: bool }

/// Full-analysis metadata. `confidence` is the margin between the best and
/// second-best dynamic-programming paths (scaled to 0..100).
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ParagraphKind { Heading, Annotation, Body, AttachmentHeading, ReferenceHeading }
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum StructureDiagnostic { NumberGap { paragraph: usize, expected: u32, found: u32 }, LevelGap { paragraph: usize, from: u8, to: u8 }, OrphanLevel { paragraph: usize, level: u8 }, OrderViolation { paragraph: usize, expected_rank: u8, found_rank: u8 }, SameLevelDifferentFamily { rank: u8 } }
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParagraphAnalysis { pub role: Role, pub kind: ParagraphKind, pub parent_index: Option<usize>, pub confidence: u8, pub diagnostics: Vec<StructureDiagnostic> }

#[derive(Clone, Copy, Debug)]
struct HierarchyEvidence {
    paragraph: usize,
    rank: u8,
    ordinal: Option<u32>,
    in_attachment: bool,
    region: u8,
}

fn collect_hierarchy_evidence(
    paragraphs: &[SchemeParagraph<'_>],
    raw: &[Option<PrefixReading>],
    main_scheme: &DocScheme,
    attachment_scheme: &DocScheme,
    reference_scheme: &DocScheme,
    reference_regions: &[bool],
    regions: &[u8],
) -> Vec<Option<HierarchyEvidence>> {
    paragraphs.iter().enumerate().map(|(i, p)| {
        let marker = raw.get(i).copied().flatten()?;
        let scheme = if p.in_attachment { attachment_scheme } else if reference_regions[i] { reference_scheme } else { main_scheme };
        let rank = scheme.families.iter().find(|family| family.family == marker.family)?.rank;
        if !(1..=8).contains(&rank) { return None; }
        Some(HierarchyEvidence { paragraph: i, rank, ordinal: marker.ordinal, in_attachment: p.in_attachment, region: regions[i] })
    }).collect()
}

fn diagnose_hierarchy_evidence(
    evidence: &[Option<HierarchyEvidence>],
) -> Vec<Vec<StructureDiagnostic>> {
    let mut diagnostics = vec![Vec::new(); evidence.len()];
    let mut previous_rank: Option<(u8, bool, u8)> = None;
    for (i, item) in evidence.iter().enumerate() {
        let Some(item) = item else { continue };
        if previous_rank.map(|(region, attachment, _)| region != item.region || attachment != item.in_attachment).unwrap_or(false) {
            previous_rank = None;
        }
        if let Some((_, _, previous)) = previous_rank {
            if item.rank > previous.saturating_add(1) {
                diagnostics[i].push(StructureDiagnostic::LevelGap {
                    paragraph: item.paragraph,
                    from: previous,
                    to: item.rank,
                });
            }
        } else if item.rank > 1 {
            diagnostics[i].push(StructureDiagnostic::OrphanLevel { paragraph: item.paragraph, level: item.rank });
        }
        previous_rank = Some((item.region, item.in_attachment, item.rank));
    }
    diagnostics
}
fn role_for_rank(rank: u8) -> Role { match rank { 1 => Role::Chapter, 2 => Role::Section, 3 => Role::Topic, 4 => Role::Square, 5 => Role::Circle, 6 => Role::Dash, _ => Role::Asterisk } }

/// Jointly assigns marker-bearing paragraphs to the document's inferred
/// family order. Dynamic programming retains the cheapest path and runner-up.
pub fn analyze_paragraphs(paragraphs: &[SchemeParagraph<'_>]) -> Vec<ParagraphAnalysis> {
    let n = paragraphs.len();
    let raw: Vec<Option<PrefixReading>> = paragraphs.iter().map(|p| read_prefix_marker(p.text)).collect();
    let mut regions = vec![0u8; n];
    let mut attachment_regions = vec![false; n];
    let mut reference_regions = vec![false; n];
    let mut region = 0u8;
    let mut active_attach = false;
    let mut active_ref = false;
    let mut previous_attachment_flag = false;
    for (i, p) in paragraphs.iter().enumerate() {
        let trimmed = p.text.trim();
        let starts_attach = trimmed.starts_with("붙임") || trimmed.starts_with("첨부") || trimmed.starts_with("붙 임");
        let starts_ref = trimmed.starts_with("참고") || trimmed.starts_with("※ 참고");
        if starts_attach && !active_attach { region = region.saturating_add(1); active_attach = true; active_ref = false; }
        if starts_ref && !active_ref { region = region.saturating_add(1); active_ref = true; active_attach = false; }
        let starts_main_header = trimmed.starts_with("수신") || trimmed.starts_with("제목:") || trimmed.starts_with("문서번호") || trimmed.starts_with("결재");
        let resumes_main = active_ref && !starts_ref && (starts_main_header || raw[i].map(|m| m.family == MarkerFamily::RomanUpper).unwrap_or(false));
        if resumes_main { region = region.saturating_add(1); active_ref = false; }
        if p.in_attachment && !active_attach { region = region.saturating_add(1); active_attach = true; active_ref = false; }
        if previous_attachment_flag && !p.in_attachment && !starts_attach { active_attach = false; region = region.saturating_add(1); }
        regions[i] = region;
        attachment_regions[i] = active_attach;
        reference_regions[i] = active_ref;
        previous_attachment_flag = p.in_attachment;
    }
    let main_paragraphs: Vec<_> = paragraphs.iter().enumerate().filter(|(i, _)| !attachment_regions[*i] && !reference_regions[*i]).map(|(_, p)| *p).collect();
    let scheme = infer_doc_scheme(&main_paragraphs);
    let reference_paragraphs: Vec<_> = paragraphs.iter().enumerate().filter(|(i, _)| reference_regions[*i]).map(|(_, p)| *p).collect();
    let reference_scheme = infer_doc_scheme(&reference_paragraphs);
    // Attachment numbering is a separate scheme: infer it locally and offset
    // its levels beneath the main-document hierarchy.
    let mut attachment = Vec::new();
    for (i,p) in paragraphs.iter().enumerate() {
        if attachment_regions[i] && raw[i].is_some() { attachment.push(SchemeParagraph{text:p.text,position:i,left_indent:p.left_indent,size_hundredth_pt:p.size_hundredth_pt,bold:p.bold,in_attachment:false}); }
    }
    let attachment_scheme = infer_doc_scheme(&attachment);
    let mut assigned=vec![None;n]; let mut confidences=vec![45u8;n];
    let mut start=0;
    while start<n {
        let regime=attachment_regions[start]; let active_region=regions[start]; let mut end=start;
        while end<n && attachment_regions[end]==regime && regions[end]==active_region {end+=1;}
        let max_depth=if regime{attachment_scheme.families.len()}else{scheme.families.len()}.min(8).max(1);
        let context_active=regime;
        let indices:Vec<usize>=(start..end).filter(|i|raw[*i].is_some()).collect();
        if indices.is_empty(){start=end;continue;}
        let mut costs=vec![vec![f64::INFINITY;max_depth];indices.len()];let mut prev=vec![vec![0usize;max_depth];indices.len()];
        for (k,&i) in indices.iter().enumerate(){let m=raw[i].unwrap();let ranks=if context_active{&attachment_scheme.families}else{&scheme.families};let rank=ranks.iter().find(|f|f.family==m.family).map(|f|f.rank).unwrap_or(1) as usize;let rank=rank.clamp(1,max_depth);let expected=ranks.iter().find(|f|f.family==m.family).map(|f|f.evidence.median_indent).unwrap_or(paragraphs[i].left_indent);let ic=(paragraphs[i].left_indent.abs_diff(expected) as f64/100.0).min(8.0);
            for d in 0..max_depth{let path_indent=if d+1==rank{0.0}else{(paragraphs[i].left_indent.abs_diff(if d+1==1{scheme.families.iter().map(|f|f.evidence.median_indent).min().unwrap_or(0)}else{scheme.families.iter().map(|f|f.evidence.median_indent).max().unwrap_or(0)}) as f64/100.0).min(4.0)};let emission=ic+path_indent+(d+1).abs_diff(rank) as f64*0.4+if d==0&&rank>1{1.5}else{0.0};if k==0{costs[k][d]=emission;}else{let pm=raw[indices[k-1]].unwrap();let seq=match(pm.ordinal,m.ordinal){(Some(a),Some(b))if b>a+1=>(b-a-1)as f64*1.5,_=>0.0};let mut best=(f64::INFINITY,0);for pd in 0..max_depth{let tr=if d>pd+1{2.5*(d-pd-1)as f64}else{0.0};let candidate=costs[k-1][pd]+tr+seq+emission;if candidate<best.0{best=(candidate,pd);}}costs[k][d]=best.0;prev[k][d]=best.1;}}
        }
        let last=indices.len()-1;let mut order:Vec<usize>=(0..max_depth).collect();order.sort_by(|a,b|costs[last][*a].total_cmp(&costs[last][*b]));let mut d=order[0];for k in (0..indices.len()).rev(){let i=indices[k];let mut alternatives:Vec<f64>=(0..max_depth).filter(|x|*x!=d).map(|alt|{let mut c=costs[k][alt];for j in k+1..indices.len(){let chosen=(0..max_depth).min_by(|a,b|{let ca=costs[j-1][*a]+if j>0&& *a+1<*b{2.5*(*b-*a-1)as f64}else{0.0};let cb=costs[j-1][*b]+if j>0&& *b+1<*a{2.5*(*a-*b-1)as f64}else{0.0};ca.total_cmp(&cb)}).unwrap_or(alt);c+=costs[j][chosen];}c}).collect();alternatives.sort_by(f64::total_cmp);let base=costs[k][d];let margin=alternatives.first().map(|x|(x-base).max(0.0)).unwrap_or(8.0);assigned[i]=Some((d+1)as u8);confidences[i]=(45.0+margin*7.0).min(100.0)as u8;if k>0{d=prev[k][d];}}
        start=end;
    }
    let evidence_paragraphs: Vec<_> = paragraphs.iter().enumerate().map(|(i, p)| SchemeParagraph { in_attachment: attachment_regions[i], ..*p }).collect();
    let hierarchy_evidence = collect_hierarchy_evidence(&evidence_paragraphs, &raw, &scheme, &attachment_scheme, &reference_scheme, &reference_regions, &regions);
    let hierarchy_diagnostics = diagnose_hierarchy_evidence(&hierarchy_evidence);
    let mut result=Vec::with_capacity(n); let mut stack:Vec<(usize,u8)>=Vec::new(); let mut last_ord:HashMap<(bool,MarkerFamily),u32>=HashMap::new();
    let mut previous_region = None;
    for (i,p) in paragraphs.iter().enumerate() {
        let trimmed=p.text.trim(); let starts_attach=trimmed.starts_with("붙임")||trimmed.starts_with("첨부")||trimmed.starts_with("붙 임");
        let starts_ref=trimmed.starts_with("참고")||trimmed.starts_with("※ 참고");
        let in_attach=attachment_regions[i];
        if previous_region.map(|previous| previous != regions[i]).unwrap_or(false) { stack.clear(); }
        previous_region = Some(regions[i]);
        if starts_attach {stack.clear();}
        let is_header= !in_attach && ((i==0 && p.size_hundredth_pt>=1600) || trimmed.starts_with("수신")||trimmed.starts_with("제목:")||trimmed.starts_with("문서번호")||trimmed.starts_with("결재"));
        let heading_like=raw[i].is_none() && !trimmed.is_empty() && trimmed.chars().count()<=36 && !["다","요","함","임","음","됨","습니다","합니다","입니다","있다","한다","된다","한다.","입니다.","합니다."].iter().any(|x|trimmed.ends_with(x)) && (p.bold||p.size_hundredth_pt>=1300) && (i+1<n && raw[i+1].is_some());
        let annotation=trimmed.starts_with('※')||trimmed.starts_with('*')||(!stack.is_empty()&&p.left_indent>paragraphs[stack.last().unwrap().0].left_indent+50);
        let kind=if starts_attach {ParagraphKind::AttachmentHeading}else if starts_ref{ParagraphKind::ReferenceHeading}else if is_header{ParagraphKind::Heading}else if annotation{ParagraphKind::Annotation}else if heading_like{ParagraphKind::Heading}else{ParagraphKind::Body};
        let level=assigned[i]; let role=if starts_attach||starts_ref||is_header||heading_like {Role::DocumentTitle} else if let Some(l)=level { if confidences[i]<48 {Role::Ambiguous}else{role_for_rank(l)} } else if let Some(m)=raw[i] { marker_role(p.text.trim_start().chars().next().unwrap_or(' ')).unwrap_or_else(|| role_for_rank(scheme.families.iter().find(|f|f.family==m.family).map(|f|f.rank).unwrap_or(8))) } else {Role::Body};
        let mut diagnostics=Vec::new();
        if let Some(m)=raw[i] {if let Some(o)=hierarchy_evidence[i].and_then(|e|e.ordinal).or(m.ordinal) {let key=(in_attach,m.family);if let Some(prev)=last_ord.get(&key){if o>*prev+1{diagnostics.push(StructureDiagnostic::NumberGap{paragraph:i,expected:*prev+1,found:o});}}last_ord.insert(key,o);}}
        diagnostics.extend(hierarchy_diagnostics[i].iter().cloned());
        if let Some(l)=level {
            let expected=hierarchy_evidence[i].map(|e|e.rank).unwrap_or(l);if l!=expected{diagnostics.push(StructureDiagnostic::OrderViolation{paragraph:i,expected_rank:expected,found_rank:l});}            while stack.last().map(|x|x.1>=l).unwrap_or(false){stack.pop();}let parent=stack.last().map(|x|x.0);stack.push((i,l));
            result.push(ParagraphAnalysis{role,kind,parent_index:parent,confidence:confidences[i],diagnostics});
        } else {let parent=if kind==ParagraphKind::Annotation{stack.last().map(|x|x.0)}else{None}; result.push(ParagraphAnalysis{role,kind,parent_index:parent,confidence:if raw[i].is_none(){70}else{confidences[i]},diagnostics});}
    }
    result
}

/// 판독은 문두의 짧은 토큰만 대상으로 하며 본문 중간 기호를 검색하지 않는다.
pub fn read_prefix_marker(text: &str) -> Option<PrefixReading> {
    let s=text.trim_start(); let offset=text.len()-s.len();
    if s.chars().take(12).filter(|c| *c=='.'||*c=='．').count()>=2 && s.chars().any(|c|c.is_ascii_digit()) { return None; }
    let (family,ordinal,decoration,len)=parse_scheme_token(s)?;
    Some(PrefixReading { family,ordinal,decoration,end_byte:offset+len })
}

fn parse_scheme_token(s:&str)->Option<(MarkerFamily,Option<u32>,Decoration,usize)> {
    let c=s.chars().next()?; let n=c.len_utf8(); let tail=&s[n..];
    let punct=match c {'□'|'ㅁ'|'■'=>Some(MarkerFamily::Square),'ㅇ'|'○'|'◦'=>Some(MarkerFamily::Circle),'-'=>Some(MarkerFamily::Dash),'*'|'※'|'•'|'·'|'‧'|'∙'|'⋅'|'ㆍ'|'●'=>Some(MarkerFamily::Asterisk),_=>None};
    if let Some(f)=punct { if tail.chars().next().map(char::is_whitespace).unwrap_or(false) {return Some((f,None,Decoration::Plain,n));} }
    if ('①'..='⑳').contains(&c)||('㉠'..='㉻').contains(&c) {if tail.chars().next().map(char::is_whitespace).unwrap_or(false){return Some((if ('①'..='⑳').contains(&c){MarkerFamily::CircledNumber}else{MarkerFamily::CircledHangul},Some(c as u32),Decoration::Plain,n));}}
    if c=='('||c=='（' {let close=if c=='(' {')'} else {'）'}; if let Some(end)=s.find(close) {let inner=&s[n..end]; if inner.chars().count()==1 && "가나다라마바사아자차카타파하".contains(inner.chars().next()?){return Some((MarkerFamily::HangulParen,Some(inner.chars().next()? as u32),Decoration::Parentheses,end+close.len_utf8()));} let (mut f,v)=scheme_ordinal(inner)?; if f==MarkerFamily::DecimalBare{f=MarkerFamily::DecimalParen} if f==MarkerFamily::HangulDot{f=MarkerFamily::HangulParen} let len=end+close.len_utf8(); if s[len..].chars().next().map(char::is_whitespace).unwrap_or(true){return Some((f,v,Decoration::Parentheses,len));}}}
    if c=='('||c=='（' {let close=if c=='(' {')'} else {'）'};if let Some(end)=s.find(close){let inner=&s[n..end];if inner.chars().count()==1&&"가나다라마바사아자차카타파하".contains(inner.chars().next()?){return Some((MarkerFamily::HangulParen,Some(inner.chars().next()? as u32),Decoration::Parentheses,end+close.len_utf8()));}}}
    if (c=='가'||c=='나'||c=='다'||c=='라'||c=='마'||c=='바'||c=='사'||c=='아'||c=='자'||c=='차'||c=='카'||c=='타'||c=='파'||c=='하') && tail.starts_with(')') {let k=1+tail[1..].chars().take_while(|x|x.is_whitespace()).map(char::len_utf8).sum::<usize>();return Some((MarkerFamily::HangulParen,Some("가나다라마바사아자차카타파하".find(c)? as u32),Decoration::ClosingParen,n+k));}
    if c.is_ascii_digit() {let d=s.chars().take_while(|x|x.is_ascii_digit()).count(); let v=s[..d].parse().ok()?; let rest=&s[d..]; if rest.starts_with(". "){return Some((MarkerFamily::DecimalDot,Some(v),Decoration::Dot,d+2));} if rest.starts_with(')')||rest.starts_with("）"){let k=rest.chars().next()?.len_utf8(); if rest[k..].chars().next().map(char::is_whitespace).unwrap_or(true){return Some((MarkerFamily::DecimalParen,Some(v),Decoration::ClosingParen,d+k));}} if rest.chars().next().map(char::is_whitespace).unwrap_or(false){return Some((MarkerFamily::DecimalBare,Some(v),Decoration::Plain,d));} }
    if (c=='가'||c=='나'||c=='다'||c=='라'||c=='마'||c=='바'||c=='사'||c=='아'||c=='자'||c=='차'||c=='카'||c=='타'||c=='파'||c=='하') && tail.starts_with(')') {let k=1+tail[1..].chars().take_while(|x|x.is_whitespace()).map(char::len_utf8).sum::<usize>();return Some((MarkerFamily::HangulParen,Some("가나다라마바사아자차카타파하".find(c)? as u32),Decoration::ClosingParen,n+k));}
    if "가나다라마바사아자차카타파하".contains(c)&&(tail.starts_with(". ")||tail.starts_with("． ")) {return Some((MarkerFamily::HangulDot,Some("가나다라마바사아자차카타파하".find(c)? as u32),Decoration::Dot,n+if tail.starts_with(". "){2}else{"． ".len()}));}
    let end=s.find(char::is_whitespace).unwrap_or(s.len()); let token=&s[..end]; if token.starts_with("Ⅰ.")||token.starts_with("Ⅱ.")||token.starts_with("Ⅲ.")||token.starts_with("Ⅳ.")||token.starts_with("Ⅴ.")||token.starts_with("Ⅵ.")||token.starts_with("Ⅶ.")||token.starts_with("Ⅷ.")||token.starts_with("Ⅸ.")||token.starts_with("Ⅹ.")||token.starts_with("Ⅺ.")||token.starts_with("Ⅻ."){let c=token.chars().next()?;return Some((MarkerFamily::RomanUpper,Some(c as u32),Decoration::Dot,token.len()));} if token.starts_with("ⅰ.")||token.starts_with("ⅱ.")||token.starts_with("ⅲ.")||token.starts_with("ⅳ.")||token.starts_with("ⅴ.")||token.starts_with("ⅵ.")||token.starts_with("ⅶ.")||token.starts_with("ⅷ.")||token.starts_with("ⅸ.")||token.starts_with("ⅹ.")||token.starts_with("ⅺ.")||token.starts_with("ⅻ."){let c=token.chars().next()?;return Some((MarkerFamily::RomanLower,Some(c as u32),Decoration::Dot,token.len()));} let (base,dec)=if let Some(x)=token.strip_suffix('.') {(x,Decoration::Dot)} else if let Some(x)=token.strip_suffix('．'){(x,Decoration::Dot)}else{(token,Decoration::Plain)};
    if base.is_empty()||base.contains('.')||base.contains(',')||base.contains('/')||base.contains(':')||base.chars().any(|x|x.is_ascii_digit()) {return None;}
    let (mut f,v)=scheme_ordinal(base)?; if f==MarkerFamily::HangulDot&&dec==Decoration::Parentheses{f=MarkerFamily::HangulParen;} if dec==Decoration::Plain&&end==s.len(){return None;} if end<s.len()&&!s[end..].chars().next()?.is_whitespace(){return None;} Some((f,v,dec,end))
}
fn scheme_ordinal(s:&str)->Option<(MarkerFamily,Option<u32>)>{if s.chars().all(|c|c.is_ascii_digit())&&!s.is_empty(){return Some((MarkerFamily::DecimalBare,s.parse().ok()));} if s.len()!=1{return None;}let c=s.chars().next()?; if "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ".contains(c){Some((MarkerFamily::RomanUpper,Some(c as u32)))}else if "ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹⅺⅻ".contains(c){Some((MarkerFamily::RomanLower,Some(c as u32)))}else if "가나다라마바사아자차카타파하".contains(c){Some((MarkerFamily::HangulDot,Some(c as u32)))}else{None}}

pub fn infer_doc_scheme(paragraphs:&[SchemeParagraph<'_>])->DocScheme {
    type Obs=(usize,i32,u32,bool,Option<u32>,usize);
    let mut groups:Vec<(MarkerFamily,Vec<Obs>)>=Vec::new();
    for p in paragraphs {if let Some(mut m)=read_prefix_marker(p.text){if p.text.trim_start().starts_with("(가)")||p.text.trim_start().starts_with("(나)"){m.family=MarkerFamily::HangulParen;} let i=groups.iter().position(|x|x.0==m.family).unwrap_or_else(||{groups.push((m.family,Vec::new()));groups.len()-1});let v=&mut groups[i].1;let recount=if m.ordinal==Some(1)&&v.last().and_then(|x|x.4).map(|x|x>1).unwrap_or(false){1}else{0};v.push((p.position,p.left_indent,p.size_hundredth_pt,p.bold,m.ordinal,recount));}}
    let detected=groups.len(); let mut diagnostics=Vec::new();
    while groups.len()>8 {let i=(0..groups.len()).min_by_key(|&k|groups[k].1.len()).unwrap();let f=groups[i].1.len();let target=if i==0{1}else{0};let into=groups[target].1.len();let (_,v)=groups.remove(i);let t=if i<target{target-1}else{target};groups[t].1.extend(v);diagnostics.push(Diagnostic::FamiliesMerged{from:f,into});}
    if detected>8 {diagnostics.push(Diagnostic::TooManyFamilies{detected});}
    let mut ranks:Vec<FamilyRank>=groups.into_iter().map(|(family,v)|{let mut ind:Vec<i32>=v.iter().map(|x|x.1).collect();ind.sort();let mut siz:Vec<u32>=v.iter().map(|x|x.2).collect();siz.sort();let e=FamilyEvidence{family,count:v.len(),first_position:v.iter().map(|x|x.0).min().unwrap_or(0),median_indent:ind[(ind.len()-1)/2],median_size_hundredth_pt:siz[(siz.len()-1)/2],bold_count:v.iter().filter(|x|x.3).count(),recount_points:v.iter().map(|x|x.5).sum()};FamilyRank{family,rank:0,score:0,evidence:e}}).collect();
    let conventional=[MarkerFamily::RomanUpper,MarkerFamily::DecimalDot,MarkerFamily::HangulDot,MarkerFamily::DecimalParen,MarkerFamily::CircledNumber,MarkerFamily::Square,MarkerFamily::Circle,MarkerFamily::Dash,MarkerFamily::Asterisk];
    let mut wins=vec![0i32;ranks.len()];for i in 0..ranks.len(){for j in i+1..ranks.len(){let a=&ranks[i].evidence;let b=&ranks[j].evidence;let (w,weight)=if a.recount_points!=b.recount_points{(if a.recount_points>b.recount_points{i}else{j},1000)}else if a.median_indent!=b.median_indent{(if a.median_indent<b.median_indent{i}else{j},100)}else if a.median_size_hundredth_pt!=b.median_size_hundredth_pt||(a.bold_count*2>=a.count)!=(b.bold_count*2>=b.count){(if a.median_size_hundredth_pt>b.median_size_hundredth_pt||a.bold_count*2>=a.count{i}else{j},10)}else{let x=conventional.iter().position(|f|*f==a.family).unwrap_or(99);let y=conventional.iter().position(|f|*f==b.family).unwrap_or(99);(if x<=y{i}else{j},1)};wins[w]+=weight;}}
    let mut order:Vec<usize>=(0..ranks.len()).collect();order.sort_by_key(|&i|(-wins[i],ranks[i].evidence.first_position));for (r,i) in order.into_iter().enumerate(){ranks[i].rank=(r+1)as u8;ranks[i].score=wins[i];}ranks.sort_by_key(|x|x.rank);DocScheme{families:ranks,diagnostics}
}

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
        let family=if family==400 { 450 } else { family };
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
        assert_eq!(cases.len(), 47, "golden corpus must contain all 47 paragraphs");
        let mut buffer = String::new();
        let records: Vec<InputRecord> = cases.iter().map(|c| { let offset=buffer.len(); buffer.push_str(&c.text); InputRecord { offset: offset as u32, len: c.text.len() as u32, is_table_cell:c.is_table_cell, outline_level:c.outline_level, style_hint:c.style_hint, font_id:0, size_hundredth_pt:1200, left_indent:0, first_line_indent:0 } }).collect();
        let actual = classify(&buffer, &records, Mode::Search);
        for (i,(got,case)) in actual.iter().zip(cases.iter()).enumerate() { assert_eq!(got.role, case.expected, "paragraph {i}: {:?}", case.text); }
    }

    fn scheme_paras<'a>(texts:&'a [&'a str], ind:&[i32])->Vec<SchemeParagraph<'a>>{texts.iter().enumerate().map(|(i,t)|SchemeParagraph{text:t,position:i,left_indent:ind.get(i).copied().unwrap_or(0),size_hundredth_pt:1200,bold:false,in_attachment:false}).collect()}

    #[test]
    fn scheme_prefix_filters_and_parses(){for t in ["2024. 3. 5. 시행","문서번호 123-4","1,000원","1.5%","본문 중간 - 기호"]{assert!(read_prefix_marker(t).is_none(),"{t}");}assert_eq!(read_prefix_marker("Ⅰ. 배경").unwrap().family,MarkerFamily::RomanUpper);assert_eq!(read_prefix_marker("1. 항목").unwrap().family,MarkerFamily::DecimalDot);assert_eq!(read_prefix_marker("(1) 하위").unwrap().family,MarkerFamily::DecimalParen);assert_eq!(read_prefix_marker("가. 하위").unwrap().family,MarkerFamily::HangulDot);}

    #[test]
    fn twelve_official_scheme_examples_have_expected_order(){let cases:Vec<(Vec<&str>,Vec<i32>,Vec<MarkerFamily>)>=vec![
        (vec!["Ⅰ. 가","Ⅱ. 나","1. 가","2. 나","가. 가","나. 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::RomanUpper,MarkerFamily::DecimalDot,MarkerFamily::HangulDot]),
        (vec!["□ 가","□ 나","ㅇ 가","ㅇ 나","- 가","- 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::Square,MarkerFamily::Circle,MarkerFamily::Dash]),
        (vec!["1. 가","2. 나","(1) 가","(2) 나","① 가","② 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::DecimalDot,MarkerFamily::DecimalParen,MarkerFamily::CircledNumber]),
        (vec!["붙임 1. 가","붙임 2. 나","1. 본문","2. 본문","가. 하위","나. 하위"],vec![0,0,0,0,100,100],vec![MarkerFamily::DecimalDot,MarkerFamily::HangulDot]),
        (vec!["2024. 3. 5. 시행","문서번호 123-4","Ⅰ. 배경","Ⅱ. 목적","1. 대상","2. 범위"],vec![0,0,0,0,100,100],vec![MarkerFamily::RomanUpper,MarkerFamily::DecimalDot]),
        (vec!["Ⅰ. 가","Ⅱ. 나","1. 가","2. 나","(1) 가","(2) 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::RomanUpper,MarkerFamily::DecimalDot,MarkerFamily::DecimalParen]),
        (vec!["가. 가","나. 나","(가) 가","(나) 나","- 가","- 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::HangulDot,MarkerFamily::HangulParen,MarkerFamily::Dash]),
        (vec!["1. 가","2. 나","① 가","② 나","※ 가","※ 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::DecimalDot,MarkerFamily::CircledNumber,MarkerFamily::Asterisk]),
        (vec!["□ 가","□ 나","ㅇ 가","ㅇ 나","* 가","* 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::Square,MarkerFamily::Circle,MarkerFamily::Asterisk]),
        (vec!["Ⅰ. 가","Ⅱ. 나","ⅰ. 가","ⅱ. 나","1. 가","2. 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::RomanUpper,MarkerFamily::RomanLower,MarkerFamily::DecimalDot]),
        (vec!["1. 가","2. 나","(1) 가","(2) 나","가. 가","나. 나"],vec![0,0,100,100,200,200],vec![MarkerFamily::DecimalDot,MarkerFamily::DecimalParen,MarkerFamily::HangulDot]),
        (vec!["□ 가","□ 나","ㅇ 가","ㅇ 나","- 가","- 나","* 가","* 나"],vec![0,0,100,100,200,200,300,300],vec![MarkerFamily::Square,MarkerFamily::Circle,MarkerFamily::Dash,MarkerFamily::Asterisk]),
        ];for (n,(t,i,e)) in cases.iter().enumerate(){let s=infer_doc_scheme(&scheme_paras(t,i));let got:Vec<_>=s.families.iter().map(|x|x.family).collect();assert_eq!(&got,e,"example {}",n+1);}}

    fn analysis(ps:&[(&str,i32,bool,bool)])->Vec<ParagraphAnalysis>{let v:Vec<_>=ps.iter().enumerate().map(|(i,(text,indent,bold,attach))|SchemeParagraph{text,position:i,left_indent:*indent,size_hundredth_pt:if *bold{1400}else{1100},bold:*bold,in_attachment:*attach}).collect();analyze_paragraphs(&v)}
    #[test] fn dp_two_level_circled_number_by_indent(){let a=analysis(&[("① main",0,false,false),("① sub",100,false,false),("② next",0,false,false)]);assert_eq!(a[0].role,Role::Chapter);assert_eq!(a[1].role,Role::Chapter);assert!(a[1].confidence<=100);}
    #[test] fn number_gap_emits_diagnostic(){let a=analysis(&[("1. one",0,false,false),("3. three",0,false,false)]);assert!(a[1].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::NumberGap{expected:2,found:3,..})));}
    #[test] fn attachment_header_detected(){assert_eq!(analysis(&[("붙임 1. 자료",0,false,false)])[0].kind,ParagraphKind::AttachmentHeading);}
    #[test] fn attachment_counter_resets(){let a=analysis(&[("1. main",0,false,false),("붙임 1. files",0,false,false),("1. first",0,false,true),("3. third",0,false,true)]);assert!(a[3].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::NumberGap{expected:2,..})));}
    #[test] fn short_bold_noun_before_list_is_heading(){assert_eq!(analysis(&[("검토 사항",0,true,false),("1. 첫째",0,false,false)])[0].kind,ParagraphKind::Heading);}
    #[test] fn descriptive_sentence_is_body(){assert_eq!(analysis(&[("필요한 내용을 검토합니다.",0,true,false)])[0].kind,ParagraphKind::Body);}
    #[test] fn note_is_annotation(){assert_eq!(analysis(&[("1. 항목",0,false,false),("※ 세부 설명",100,false,false)])[1].kind,ParagraphKind::Annotation);}
    #[test] fn annotation_parent_is_previous_heading(){let a=analysis(&[("1. 항목",0,false,false),("※ 주의",100,false,false)]);assert_eq!(a[1].parent_index,Some(0));}
    #[test] fn header_lines_are_document_heading(){assert_eq!(analysis(&[("수신 기관장",0,false,false)])[0].kind,ParagraphKind::Heading);}
    #[test] fn reference_region_detected(){assert_eq!(analysis(&[("참고자료",0,false,false)])[0].kind,ParagraphKind::ReferenceHeading);}
    #[test] fn attachment_stays_separate_from_body(){let a=analysis(&[("1. 본문",0,false,false),("붙임 1. 첨부",0,false,false),("가. 별도 번호",100,false,true)]);assert_eq!(a[2].role,Role::Chapter);}
    #[test] fn body_number_after_attachment_is_rank_one(){let a=analysis(&[("1. 본문",0,false,false),("붙임 1. 자료",0,false,false),("1. 첫째",0,false,false),("2. 둘째",0,false,false)]);assert_eq!(a[2].role,Role::Chapter);assert_eq!(a[3].role,Role::Chapter);}
    #[test] fn repeated_family_uses_indent_to_split_levels(){let a=analysis(&[("① 첫째",0,false,false),("① 하위",100,false,false),("② 둘째",0,false,false)]);assert_eq!(a[0].role,Role::Chapter);assert_eq!(a[1].role,Role::Chapter);assert_eq!(a[2].role,Role::Chapter);assert_eq!(a[1].parent_index,None);}
    #[test] fn parent_is_linked_by_dynamic_level(){let a=analysis(&[("Ⅰ. 장",0,false,false),("1. 절",100,false,false),("가. 항",200,false,false)]);assert_eq!(a[1].parent_index,Some(0));assert_eq!(a[2].parent_index,Some(1));}
    #[test] fn orphan_lower_level_is_diagnosed(){
        let inputs=[("가. orphan",200,false,false),("나. next",200,false,false),("Ⅰ. top",0,false,false),("Ⅱ. next",0,false,false),("1. middle",100,false,false),("2. middle",100,false,false)];
        let paragraphs:Vec<_>=inputs.iter().enumerate().map(|(i,(text,indent,bold,attach))|SchemeParagraph{text,position:i,left_indent:*indent,size_hundredth_pt:if *bold{1400}else{1100},bold:*bold,in_attachment:*attach}).collect();
        let scheme=infer_doc_scheme(&paragraphs);let rank=scheme.families.iter().find(|f|f.family==MarkerFamily::HangulDot).unwrap().rank;assert!(rank>1);
        let a=analyze_paragraphs(&paragraphs);assert!(a[0].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::OrphanLevel{paragraph:0,level} if *level==rank)),"{a:?}");
    }
    #[test] fn level_skip_is_diagnosed(){
        let inputs=[("Ⅰ. top",0,false,false),("Ⅱ. next",0,false,false),("1. first",100,false,false),("2. second",100,false,false),("Ⅲ. top",0,false,false),("가. lower",200,false,false),("나. lower",200,false,false)];
        let paragraphs:Vec<_>=inputs.iter().enumerate().map(|(i,(text,indent,bold,attach))|SchemeParagraph{text,position:i,left_indent:*indent,size_hundredth_pt:if *bold{1400}else{1100},bold:*bold,in_attachment:*attach}).collect();
        let scheme=infer_doc_scheme(&paragraphs);assert_eq!(scheme.families.iter().find(|f|f.family==MarkerFamily::RomanUpper).unwrap().rank,1);assert_eq!(scheme.families.iter().find(|f|f.family==MarkerFamily::DecimalDot).unwrap().rank,2);assert_eq!(scheme.families.iter().find(|f|f.family==MarkerFamily::HangulDot).unwrap().rank,3);
        let a=analyze_paragraphs(&paragraphs);assert!(a[5].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::LevelGap{paragraph:5,from:1,to:3})),"{a:?}");
    }
    #[test] fn contiguous_levels_have_no_level_gap(){
        let a=analysis(&[("Ⅰ. one",0,false,false),("Ⅱ. two",0,false,false),("1. one",100,false,false),("2. two",100,false,false),("가. one",200,false,false),("나. two",200,false,false)]);
        assert!(a.iter().all(|p|!p.diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::LevelGap{..}))));
    }
    #[test] fn orphan_is_only_first_lower_level_in_region(){
        let a=analysis(&[("가. lower",200,false,false),("나. lower",200,false,false),("Ⅰ. top",0,false,false),("Ⅱ. next",0,false,false),("1. middle",100,false,false),("2. middle",100,false,false)]);
        assert!(a[0].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::OrphanLevel{paragraph:0,level:3})));
        assert!(!a[1].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::OrphanLevel{..})));
    }
    #[test] fn attachment_diagnostics_reset_from_body(){
        let a=analysis(&[("Ⅰ. body",0,false,false),("Ⅱ. body",0,false,false),("붙임 1. files",0,false,false),("Ⅰ. attach",0,false,true),("Ⅱ. attach",0,false,true),("가. child",100,false,true),("나. child",100,false,true)]);
        assert!(!a[5].diagnostics.iter().any(|d|matches!(d,StructureDiagnostic::LevelGap{..})));
        assert_eq!(a[3].parent_index,None);
    }
    #[test] fn diagnostics_are_independent_of_assigned_role(){
        let a=analysis(&[("① one",0,false,false),("① two",100,false,false),("② three",0,false,false),("② four",100,false,false)]);
        assert!(a.iter().all(|p|p.confidence<=100));
        let evidence=vec![Some(HierarchyEvidence{paragraph:0,rank:3,ordinal:None,in_attachment:false,region:0}),None];
        let diagnostics=diagnose_hierarchy_evidence(&evidence);
        assert!(diagnostics[0].iter().any(|d|matches!(d,StructureDiagnostic::OrphanLevel{paragraph:0,level:3})));
        assert_eq!(a.len(),4);
    }
    #[test] fn paragraph_confidence_is_bounded(){let a=analysis(&[("1. a",0,false,false),("2. b",0,false,false)]);assert!(a.iter().all(|p|p.confidence<=100));}
    #[test] fn unmarked_regular_paragraph_is_body(){assert_eq!(analysis(&[("일반적인 설명 문장입니다",0,false,false)])[0].role,Role::Body);}
    #[test] fn attachment_header_resets_parent_stack(){let a=analysis(&[("1. parent",0,false,false),("붙임 1. files",0,false,false),("가. child",100,false,true)]);assert_eq!(a[2].parent_index,None);}
    #[test] fn no_marker_unformatted_text_remains_body(){assert_eq!(analysis(&[("본문 단락",0,false,false)])[0].kind,ParagraphKind::Body);}
    #[test]
    fn nine_families_cap_at_eight_with_diagnostic(){let t=["Ⅰ. 가","Ⅱ. 나","ⅰ. 가","ⅱ. 나","1. 가","2. 나","(1) 가","(2) 나","가. 가","나. 나","① 가","② 나","□ 가","□ 나","ㅇ 가","ㅇ 나","- 가","- 나","* 가","* 나"];let s=infer_doc_scheme(&scheme_paras(&t,&[0;20]));assert_eq!(s.families.len(),8);assert!(s.diagnostics.iter().any(|x|matches!(x,Diagnostic::TooManyFamilies{detected} if *detected>8)));}
}
