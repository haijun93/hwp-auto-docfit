//! Pure notebook paragraph transformations.

use regex::Regex;
use std::collections::HashMap;
use std::sync::OnceLock;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Para {
    pub source_id: String,
    pub seq: u64,
    pub page: Option<u64>,
    pub level: Option<u8>,
    pub text: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OutlineItem {
    pub source_id: String,
    pub seq: u64,
    pub page: Option<u64>,
    pub level: u8,
    pub indent: usize,
    pub text: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TableGroup {
    pub source_id: String,
    pub rows: Vec<Vec<String>>,
    pub paragraph_seqs: Vec<u64>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TextHit {
    pub source_id: String,
    pub seq: u64,
    pub page: Option<u64>,
    pub text: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Keyword {
    pub term: String,
    pub count: usize,
}

pub fn outline(paras: &[Para]) -> Vec<OutlineItem> {
    paras.iter().filter_map(|para| para.level.map(|level| OutlineItem {
        source_id: para.source_id.clone(), seq: para.seq, page: para.page, level,
        indent: usize::from(level) * 2, text: para.text.clone(),
    })).collect()
}

fn split_cells(text: &str) -> Option<Vec<String>> {
    if !text.contains('|') && !text.contains('\t') { return None; }
    let trimmed = text.trim();
    let body = if trimmed.starts_with('|') && trimmed.ends_with('|') && trimmed.len() >= 2 {
        &trimmed[1..trimmed.len() - 1]
    } else { trimmed };
    let cells: Vec<String> = body.split(|c| c == '|' || c == '\t').map(|s| s.trim().to_owned()).collect();
    (cells.len() >= 2 && cells.iter().any(|s| !s.is_empty())).then_some(cells)
}

fn is_table_marked(para: &Para) -> bool {
    para.level.is_none()
        && ["[표]", "표:", "<표>"]
            .iter()
            .any(|marker| para.text.trim_start().starts_with(marker))
}

fn marked_cells(text: &str) -> Vec<String> {
    let trimmed = text.trim();
    let body = ["[표]", "표:", "<표>"]
        .iter()
        .find_map(|marker| trimmed.strip_prefix(marker))
        .unwrap_or(trimmed)
        .trim();
    split_cells(body).unwrap_or_else(|| vec![body.to_owned()])
}

pub fn tables(paras: &[Para]) -> Vec<TableGroup> {
    let mut result: Vec<TableGroup> = Vec::new();
    let mut previous: Option<(String, u64)> = None;
    let mut previous_marked = false;
    for para in paras {
        let marked = is_table_marked(para);
        let cells = split_cells(&para.text).or_else(|| marked.then(|| marked_cells(&para.text)));
        match cells {
            Some(row) => {
                let contiguous = previous.as_ref().is_some_and(|(source, seq)| source == &para.source_id && seq.checked_add(1) == Some(para.seq));
                if contiguous && marked == previous_marked && result.last().is_some_and(|group| group.source_id == para.source_id) {
                    let group = result.last_mut().expect("group exists when contiguous");
                    group.rows.push(row);
                    group.paragraph_seqs.push(para.seq);
                } else {
                    result.push(TableGroup { source_id: para.source_id.clone(), rows: vec![row], paragraph_seqs: vec![para.seq] });
                }
                previous = Some((para.source_id.clone(), para.seq));
                previous_marked = marked;
            }
            None => { previous = None; previous_marked = false; }
        }
    }
    result
}

fn number_pattern() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?x)(?:\d{4}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{1,2}\.?|\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?|\d{1,2}\s*일|\d{1,2}\s*분기|\d{4}\s*년|(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\s*\d+)?\s*(?:원|만원|천원|억원|달러|USD|%|퍼센트|대비\s*[:/]\s*\d+)? )").expect("valid numeric pattern"))
}

pub fn numbers(paras: &[Para]) -> Vec<TextHit> {
    paras.iter().filter(|p| !p.text.trim().is_empty() && number_pattern().is_match(&p.text)).map(|p| TextHit {
        source_id: p.source_id.clone(), seq: p.seq, page: p.page, text: p.text.clone(),
    }).collect()
}

// 조사 목록은 요구된 어미 목록(은는이가을를의에서로와과도)을 그대로 반영한다.
const STOPWORDS: &[&str] = &[
    "및", "또는", "대한", "통해", "경우", "위해", "따라", "관련", "대해",
    "있다", "있는", "있으며", "한다", "하는", "합니다", "됩니다", "것", "수",
];
const PARTICLES: &[&str] = &["에서", "으로", "은", "는", "이", "가", "을", "를", "의", "로", "와", "과", "도"];
const QUESTION_WORDS: &[&str] = &["무엇", "어떻게", "왜", "언제"];

fn raw_tokens(text: &str) -> Vec<String> {
    static WORD_RE: OnceLock<Regex> = OnceLock::new();
    let re = WORD_RE.get_or_init(|| Regex::new(r"[가-힣A-Za-z]+(?:'[A-Za-z]+)?").expect("valid word pattern"));
    re.find_iter(text).map(|m| m.as_str().to_lowercase()).collect()
}

fn normalize_token(raw: &str) -> Option<String> {
    let mut token = raw.to_owned();
    if let Some(particle) = PARTICLES.iter().filter(|p| token.ends_with(**p)).max_by_key(|p| p.len()) {
        token.truncate(token.len() - particle.len());
    }
    (token.chars().count() >= 2 && !STOPWORDS.contains(&token.as_str())).then_some(token)
}

fn tokens(text: &str) -> Vec<String> {
    raw_tokens(text).iter().filter_map(|raw| normalize_token(raw)).collect()
}

fn is_question_expression(raw: &str) -> bool {
    ["무엇", "어떻게", "왜", "언제", "무엇이", "무엇을", "무엇은", "어떻게는", "어떻게든", "왜냐하면", "언제든"]
        .iter().any(|form| raw == *form || raw.starts_with(form))
}

pub fn keywords(paras: &[Para], n: usize) -> Vec<Keyword> {
    if n == 0 { return Vec::new(); }
    let mut counts: HashMap<String, usize> = HashMap::new();
    for para in paras { for token in tokens(&para.text) { *counts.entry(token).or_default() += 1; } }
    let mut result: Vec<Keyword> = counts.into_iter().map(|(term, count)| Keyword { term, count }).collect();
    result.sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.term.cmp(&b.term)));
    result.truncate(n);
    result
}

pub fn query_terms(question: &str) -> Vec<String> {
    let mut seen = std::collections::HashSet::new();
    let mut result = Vec::new();
    for raw in raw_tokens(question) {
        if is_question_expression(&raw) { continue; }
        if let Some(term) = normalize_token(&raw) {
            if !QUESTION_WORDS.contains(&term.as_str()) && seen.insert(term.clone()) { result.push(term); }
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    fn p(seq: u64, level: Option<u8>, text: &str) -> Para {
        Para { source_id: "공문".into(), seq, page: Some(1), level, text: text.into() }
    }

    #[test]
    fn outline_keeps_only_explicit_levels_and_order() {
        let got = outline(&[p(1, Some(0), "제1조 목적"), p(2, Some(1), "가. 적용 범위"), p(3, None, "본문 설명"), p(4, Some(2), "1) 세부 기준")]);
        assert_eq!(got.len(), 3);
        assert_eq!(got.iter().map(|x| x.indent).collect::<Vec<_>>(), vec![0, 2, 4]);
        assert_eq!(got[1].text, "가. 적용 범위");
        assert_eq!(got[2].seq, 4);
    }

    #[test]
    fn outline_handles_public_notice_hierarchy_examples() {
        let got = outline(&[
            p(1, Some(0), "제1조(목적)"),
            p(2, Some(1), "① 지원 대상"),
            p(3, Some(2), "가. 신청 방법"),
        ]);
        assert_eq!(got.iter().map(|item| item.indent).collect::<Vec<_>>(), vec![0, 2, 4]);
    }

    #[test]
    fn outline_preserves_source_page_and_text() {
        let got = outline(&[p(7, Some(1), "제2항 지원 절차")]);
        assert_eq!(got[0].source_id, "공문");
        assert_eq!(got[0].page, Some(1));
        assert_eq!(got[0].text, "제2항 지원 절차");
    }

    #[test]
    fn tables_groups_delimited_rows_by_source_and_sequence() {
        let rows = tables(&[p(1, None, "항목\t내용"), p(2, None, "예산\t1,000만원"), p(3, None, "| 담당 부서 | 기획팀 |")]);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].rows[0], vec!["항목", "내용"]);
        assert_eq!(rows[0].rows.len(), 3);
        assert_eq!(rows[0].paragraph_seqs, vec![1, 2, 3]);
    }

    #[test]
    fn tables_preserves_empty_cells_and_splits_boundaries() {
        let mut other = p(5, None, "부서|담당"); other.source_id = "별도".into();
        let got = tables(&[p(1, None, "구분||비고"), p(3, None, "항목|내용"), other, p(6, None, "일반 문장")]);
        assert_eq!(got.len(), 3);
        assert_eq!(got[0].rows[0], vec!["구분", "", "비고"]);
    }

    #[test]
    fn tables_accepts_explicit_table_markers_without_levels() {
        let got = tables(&[
            p(1, None, "[표] 사업 추진 일정"),
            p(2, None, "표: 예산 집행 현황"),
            p(3, None, "<표> 부서별 담당 업무"),
        ]);
        assert_eq!(got.len(), 1);
        assert_eq!(got[0].rows.len(), 3);
        assert_eq!(got[0].rows[0], vec!["[표] 사업 추진 일정"]);
    }

    #[test]
    fn tables_keeps_marked_rows_together_and_excludes_following_prose() {
        let got = tables(&[
            p(1, None, "[표] 항목\t내용"),
            p(2, None, "예산\t1,250만원"),
            p(3, None, "담당 부서는 기획팀입니다."),
            p(4, None, "표: 일정|담당"),
            p(5, None, "11월|사업부서"),
        ]);
        assert_eq!(got.len(), 2);
        assert_eq!(got[0].rows, vec![vec!["항목", "내용"], vec!["예산", "1,250만원"]]);
        assert_eq!(got[0].paragraph_seqs, vec![1, 2]);
        assert_eq!(got[1].rows, vec![vec!["일정", "담당"], vec!["11월", "사업부서"]]);
    }

    #[test]
    fn numbers_finds_public_document_numeric_forms() {
        let got = numbers(&[p(1, None, "2026. 11. 5.까지 제출"), p(2, None, "사업비는 1,250만원이며 증가율은 3.5%"), p(3, None, "제3분기 실적은 전년 대비 12:10")]);
        assert_eq!(got.len(), 3);
    }

    #[test]
    fn numbers_returns_each_paragraph_once_in_input_order() {
        let got = numbers(&[p(9, None, "2026년 사업비 2억원"), p(10, None, "안내 말씀드립니다"), p(11, None, "11월 말까지 회신")]);
        assert_eq!(got.iter().map(|x| x.seq).collect::<Vec<_>>(), vec![9, 11]);
    }

    #[test]
    fn numbers_finds_month_quarter_and_official_date_forms() {
        let got = numbers(&[
            p(1, None, "2026. 11. 5.까지 신청서를 제출하십시오."),
            p(2, None, "11월 중 현장 점검을 실시합니다."),
            p(3, None, "제3분기 사업 실적을 보고하십시오."),
        ]);
        assert_eq!(got.len(), 3);
    }

    #[test]
    fn numbers_recognizes_complete_dates_before_plain_numbers() {
        let got = numbers(&[
            p(1, None, "2026-11-05부터 현장 점검을 실시합니다."),
            p(2, None, "11월 5일에 신청서를 접수합니다."),
            p(3, None, "제3분기 실적을 2026. 11. 5.까지 제출하십시오."),
        ]);
        assert_eq!(got.len(), 3);
        let date = number_pattern().find("11월 5일").expect("date is recognized").as_str();
        assert_eq!(date, "11월 5일");
        let quarter = number_pattern().find("3분기").expect("quarter is recognized").as_str();
        assert_eq!(quarter, "3분기");
    }

    #[test]
    fn keywords_removes_particles_stopwords_and_sorts() {
        let got = keywords(&[p(1, None, "사업계획은 관계기관과 협의합니다."), p(2, None, "사업계획을 검토한다."), p(3, None, "대한 지침 및 시행")], 10);
        assert_eq!(got[0], Keyword { term: "사업계획".into(), count: 2 });
        assert!(!got.iter().any(|x| ["대한", "및", "합니다"].contains(&x.term.as_str())));
    }

    #[test]
    fn keywords_breaks_ties_and_limits_top_n() {
        let got = keywords(&[p(1, None, "예산 편성 지침"), p(2, None, "성과 관리 지침"), p(3, None, "추진 계획")], 2);
        assert_eq!(got.len(), 2);
        assert_eq!(got[0].term, "관리");
        assert!(keywords(&[p(1, None, "예산 편성 지침")], 0).is_empty());
    }

    #[test]
    fn keywords_removes_each_requested_particle_and_document_stopwords() {
        let got = keywords(&[p(1, None,
            "계획은 계획는 계획이 계획가 계획을 계획를 계획의 계획에서 계획로 계획와 계획과 계획도 관련 지침에 따라 시행"),
        ], 30);
        assert_eq!(got.iter().filter(|item| item.term == "계획").map(|item| item.count).sum::<usize>(), 12);
        assert!(!got.iter().any(|item| ["관련", "따라"].contains(&item.term.as_str())));
    }

    #[test]
    fn keywords_removes_euro_particle_from_official_terms() {
        let got = keywords(&[
            p(1, None, "운영으로 예산을 배정합니다."),
            p(2, None, "운영으로 사업을 추진합니다."),
            p(3, None, "계획에 따라 집행합니다."),
        ], 20);
        assert_eq!(got.iter().find(|item| item.term == "운영").map(|item| item.count), Some(2));
        assert!(!got.iter().any(|item| item.term == "운영으로"));
    }

    #[test]
    fn query_terms_removes_question_words_and_particles() {
        let got = query_terms("예산은 무엇이며 사업계획을 어떻게 추진하는가?");
        assert!(got.contains(&"예산".to_owned()));
        assert!(got.contains(&"사업계획".to_owned()));
        assert!(!got.iter().any(|x| QUESTION_WORDS.contains(&x.as_str())));
    }

    #[test]
    fn query_terms_deduplicates_and_handles_empty_question() {
        let got = query_terms("예산과 예산의 집행 시기는 언제인가?");
        assert_eq!(got.iter().filter(|x| *x == "예산").count(), 1);
        assert!(!got.contains(&"언제".to_owned()));
        assert!(query_terms("").is_empty());
    }

    #[test]
    fn query_terms_extracts_terms_from_official_question() {
        let got = query_terms("지원 대상은 무엇이며 신청 절차를 어떻게 안내합니까?");
        assert!(got.contains(&"지원".to_owned()));
        assert!(got.contains(&"대상".to_owned()));
        assert!(got.contains(&"신청".to_owned()));
        assert!(got.contains(&"절차".to_owned()));
        assert!(!got.iter().any(|term| QUESTION_WORDS.contains(&term.as_str())));
    }

    #[test]
    fn query_terms_removes_conjugated_question_expressions() {
        let got = query_terms("왜 예산이 필요한가? 신청 절차는 어떻게 추진합니까? 무엇을 제출해야 하는지 언제 정합니까?");
        assert!(got.contains(&"예산".to_owned()));
        assert!(got.contains(&"신청".to_owned()));
        assert!(got.contains(&"절차".to_owned()));
        assert!(!got.iter().any(|term| ["어떻게", "무엇", "무엇을", "언제", "왜"].contains(&term.as_str())));
    }
}
