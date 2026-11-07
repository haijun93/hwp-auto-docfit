//! 빠른 목록 분류 규칙 코어(플랫폼 독립: Windows API·파일 시스템 직접 접근 없음).
//!
//! 항목 → 분류(전체·문서·그림·파일·폴더·웹·화면캡처) 판별, 키워드 검색(한글 조합·대소문자 무시), 최신순 정렬.
//! 파일/폴더 구분이 필요하면 호출하는 쪽이 `is_dir` 함수를 주입한다(시험은 가짜 함수).
//!
//! 정한 규칙(사용자 확인 전 '기본안'; 바꿀 때는 이 목록과 시험을 함께 고친다):
//! 1. 분류는 겹칠 수 있다. 한 항목이 여러 분류에 속하고, "전체"에는 항상 속한다.
//! 2. 화면캡처: kind=image 이면서 source=="screenshot"·캡처 프로그램(ScreenClippingHost·캡처 도구) 또는
//!    미리보기가 "캡처 · "로 시작. 그림에도 함께 속한다.
//! 3. 그림: kind=image, 또는 파일 항목에 그림 확장자 파일이 하나라도 있음.
//! 4. 문서: 파일 항목에 문서 확장자 파일이 하나라도 있음, 또는 글 항목이 문서 프로그램(source)에서 왔거나
//!    문서 서식(한/글·엑셀·RTF)을 가짐. 브라우저 HTML만 있는 글은 문서가 아니라 웹.
//! 5. 파일/폴더: 파일 항목에 폴더가 아닌 경로가 하나라도 있으면 파일, 폴더가 하나라도 있으면 폴더(섞이면 둘 다).
//!    폴더 여부는 `is_dir`(Some(true)=폴더, Some(false)=파일, None=알 수 없음)로, None이면 경로 끝 구분자·확장자로
//!    추정: 끝이 \ 또는 / 이거나 드라이브 루트이면 폴더, 확장자가 없으면 폴더, 있으면 파일.
//! 6. 웹: 저장된 출처 주소(web_url)가 있음, 미리보기에 " · 웹 · " 표식, 또는 글 전체가 http(s) 주소 한 개,
//!    또는 브라우저(source)에서 온 HTML 서식 글.
//! 7. 정렬: 고정(핀) 여부와 무관하게 순수 최신순(sort_time 내림차순, 같으면 id 내림차순). 핀 우선은 호출 쪽 몫.
//! 8. 검색: 공백으로 나눈 낱말을 모두 포함(AND). 대상은 미리보기·파일 전체 경로·웹 주소(source 프로그램 이름은 제외).
//!    대소문자 무시, 한글은 자모로 풀어 비교하므로 조합 중인 글자("한ㄱ", "하")도 "한글"에 맞고
//!    macOS식 분해형(NFD) 글자와도 같다. 부작용: "하"가 "한"에도 맞는다(조합 중 입력 허용을 위한 선택).
#![allow(dead_code)]

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Category {
    All,
    Document,
    Image,
    File,
    Folder,
    Web,
    Capture,
}

impl Category {
    pub const ALL: [Category; 7] = [Category::All, Category::Document, Category::Image, Category::File,
                                    Category::Folder, Category::Web, Category::Capture];

    /// 분류 단추에 쓸 이름.
    pub fn label(self) -> &'static str {
        match self {
            Category::All => "전체",
            Category::Document => "문서",
            Category::Image => "그림",
            Category::File => "파일",
            Category::Folder => "폴더",
            Category::Web => "웹",
            Category::Capture => "화면캡처",
        }
    }

    fn bit(self) -> u8 {
        1 << (self as u8)
    }
}

/// 항목이 속한 분류 집합.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct CategorySet(u8);

impl CategorySet {
    /// 주어진 분류들로 만든 집합("전체"는 넣지 않으면 빠진다 — 시험·호출 쪽 편의용).
    pub fn of(cats: &[Category]) -> CategorySet {
        let mut s = CategorySet::default();
        for c in cats {
            s.insert(*c);
        }
        s
    }
    pub fn contains(self, c: Category) -> bool {
        self.0 & c.bit() != 0
    }
    fn insert(&mut self, c: Category) {
        self.0 |= c.bit();
    }
}

/// 분류·검색에 필요한 항목 정보(저장소 Summary + 출처·서식 이름·경로를 호출 쪽에서 채움).
#[derive(Clone, Debug, Default)]
pub struct Entry {
    pub id: i64,
    /// "text" | "image" | "files"
    pub kind: String,
    pub preview: String,
    /// 소문자 프로그램 파일 이름(예: "winword.exe"), 화면 캡처는 "screenshot".
    pub source: String,
    /// 정렬 기준 시각(초).
    pub sort_time: f64,
    /// 함께 보관한 클립보드 서식 이름("HTML Format", "Rich Text Format" 등).
    pub formats: Vec<String>,
    /// 파일 항목의 전체 경로.
    pub paths: Vec<String>,
    /// 저장해 둔 출처 주소(검증된 http/https).
    pub web_url: Option<String>,
    /// 글 항목 본문(주소 판별용, 없으면 빈 문자열).
    pub text: String,
}

const DOC_EXTS: &[&str] = &[
    "hwp", "hwpx", "hml", "hwt", "doc", "docx", "dot", "dotx", "docm", "xls", "xlsx", "xlsm", "xlsb", "csv",
    "ppt", "pptx", "pps", "ppsx", "pdf", "txt", "rtf", "md", "odt", "ods", "odp", "one", "gul", "show", "cell",
    "xps", "epub",
];
const IMAGE_EXTS: &[&str] = &["png", "jpg", "jpeg", "jpe", "gif", "bmp", "webp", "tif", "tiff", "ico", "svg", "heic", "heif", "avif"];
const DOC_PROGRAMS: &[&str] = &[
    "hwp.exe", "hwpviewer.exe", "hword.exe", "hcell.exe", "hshow.exe", "winword.exe", "excel.exe", "powerpnt.exe",
    "onenote.exe", "soffice.exe", "soffice.bin", "swriter.exe", "scalc.exe", "simpress.exe", "acrobat.exe",
    "acrord32.exe", "acrord64.exe", "foxitreader.exe", "foxitpdfreader.exe", "wordpad.exe", "hancomoffice.exe",
];
const BROWSERS: &[&str] = &[
    "chrome.exe", "msedge.exe", "firefox.exe", "whale.exe", "brave.exe", "opera.exe", "vivaldi.exe",
    "iexplore.exe", "safari",
];
/// 클립보드 주인이 이 프로그램이면 화면 캡처(Win+Shift+S·캡처 도구)로 본다.
const CAPTURE_PROGRAMS: &[&str] = &["screenclippinghost.exe", "snippingtool.exe", "screensketch.exe"];
const DOC_FORMATS: &[&str] =&["hwp character shape", "hwp native", "hwp format", "hwp paragraph shape", "rich text format",
                               "xml spreadsheet", "biff8", "biff12", "csv"];

/// 경로의 파일 이름(\ 와 / 모두 구분자).
fn file_name(path: &str) -> &str {
    let trimmed = path.trim_end_matches(['\\', '/']);
    trimmed.rsplit(['\\', '/']).next().unwrap_or(trimmed)
}

/// 소문자 확장자(없거나 ".gitignore"처럼 점으로만 시작하면 None).
pub fn extension(path: &str) -> Option<String> {
    let name = file_name(path);
    let dot = name.rfind('.')?;
    if dot == 0 || dot + 1 == name.len() {
        return None;
    }
    Some(name[dot + 1..].to_lowercase())
}

fn guess_is_dir(path: &str) -> bool {
    if path.ends_with(['\\', '/']) {
        return true;
    }
    let b = path.as_bytes();
    if b.len() == 2 && b[1] == b':' {
        return true; // "C:"
    }
    extension(path).is_none()
}

fn path_is_dir(path: &str, is_dir: &dyn Fn(&str) -> Option<bool>) -> bool {
    is_dir(path).unwrap_or_else(|| guess_is_dir(path))
}

fn is_single_web_url(text: &str) -> bool {
    let t = text.trim();
    (t.starts_with("http://") || t.starts_with("https://")) && t.len() > 8 && !t.contains(char::is_whitespace)
}

/// 항목이 속한 분류를 모두 구한다.
pub fn classify(entry: &Entry, is_dir: &dyn Fn(&str) -> Option<bool>) -> CategorySet {
    let mut set = CategorySet::default();
    set.insert(Category::All);
    let source = entry.source.to_lowercase();
    let has_format = |names: &[&str]| entry.formats.iter().any(|f| names.iter().any(|n| f.eq_ignore_ascii_case(n)));
    match entry.kind.as_str() {
        "image" => {
            set.insert(Category::Image);
            if source == "screenshot" || CAPTURE_PROGRAMS.contains(&source.as_str()) || entry.preview.starts_with("캡처 · ") {
                set.insert(Category::Capture);
            }
        }
        "files" => {
            for path in &entry.paths {
                if path_is_dir(path, is_dir) {
                    set.insert(Category::Folder);
                } else {
                    set.insert(Category::File);
                    match extension(path) {
                        Some(ext) if DOC_EXTS.contains(&ext.as_str()) => set.insert(Category::Document),
                        Some(ext) if IMAGE_EXTS.contains(&ext.as_str()) => set.insert(Category::Image),
                        _ => {}
                    }
                }
            }
        }
        "text" => {
            if DOC_PROGRAMS.contains(&source.as_str()) || has_format(DOC_FORMATS) {
                set.insert(Category::Document);
            }
            if is_single_web_url(&entry.text) || (BROWSERS.contains(&source.as_str()) && has_format(&["html format"])) {
                set.insert(Category::Web);
            }
        }
        _ => {}
    }
    if entry.web_url.is_some() || entry.preview.contains(" · 웹 · ") {
        set.insert(Category::Web);
    }
    set
}

// ---- 검색 정규화 ----

const CHO: [&str; 19] = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"];
const JUNG: [&str; 21] = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅗㅏ", "ㅗㅐ", "ㅗㅣ", "ㅛ", "ㅜ", "ㅜㅓ", "ㅜㅔ",
                          "ㅜㅣ", "ㅠ", "ㅡ", "ㅡㅣ", "ㅣ"];
const JONG: [&str; 28] = ["", "ㄱ", "ㄲ", "ㄱㅅ", "ㄴ", "ㄴㅈ", "ㄴㅎ", "ㄷ", "ㄹ", "ㄹㄱ", "ㄹㅁ", "ㄹㅂ", "ㄹㅅ", "ㄹㅌ", "ㄹㅍ",
                          "ㄹㅎ", "ㅁ", "ㅂ", "ㅂㅅ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"];
/// 호환 자모의 겹글자(ㄳ, ㅘ 등)를 낱자로 푼다. 첫 칸이 대상, 둘째 칸이 풀이.
const COMPOUND: [(char, &str); 11 + 10] = [
    ('ㄳ', "ㄱㅅ"), ('ㄵ', "ㄴㅈ"), ('ㄶ', "ㄴㅎ"), ('ㄺ', "ㄹㄱ"), ('ㄻ', "ㄹㅁ"), ('ㄼ', "ㄹㅂ"), ('ㄽ', "ㄹㅅ"),
    ('ㄾ', "ㄹㅌ"), ('ㄿ', "ㄹㅍ"), ('ㅀ', "ㄹㅎ"), ('ㅄ', "ㅂㅅ"),
    ('ㅘ', "ㅗㅏ"), ('ㅙ', "ㅗㅐ"), ('ㅚ', "ㅗㅣ"), ('ㅝ', "ㅜㅓ"), ('ㅞ', "ㅜㅔ"), ('ㅟ', "ㅜㅣ"), ('ㅢ', "ㅡㅣ"),
    ('ㄲ', "ㄲ"), ('ㄸ', "ㄸ"), ('ㅃ', "ㅃ"),
];

/// 소문자화하고 한글을 낱자모(호환 자모)로 푼다. 완성형·분해형(NFD)·조합 중 입력이 같은 열로 바뀐다.
pub fn normalize(s: &str) -> String {
    let mut out = String::with_capacity(s.len() * 2);
    for ch in s.chars() {
        let c = ch as u32;
        if (0xAC00..=0xD7A3).contains(&c) {
            let i = c - 0xAC00;
            out.push_str(CHO[(i / 588) as usize]);
            out.push_str(JUNG[((i % 588) / 28) as usize]);
            out.push_str(JONG[(i % 28) as usize]);
        } else if (0x1100..=0x1112).contains(&c) {
            out.push_str(CHO[(c - 0x1100) as usize]);
        } else if (0x1161..=0x1175).contains(&c) {
            out.push_str(JUNG[(c - 0x1161) as usize]);
        } else if (0x11A8..=0x11C2).contains(&c) {
            out.push_str(JONG[(c - 0x11A7) as usize]);
        } else if let Some((_, rest)) = COMPOUND.iter().find(|(k, _)| *k == ch) {
            out.push_str(rest);
        } else {
            out.extend(ch.to_lowercase());
        }
    }
    out
}

fn haystack(entry: &Entry) -> String {
    let mut parts: Vec<&str> = vec![&entry.preview];
    parts.extend(entry.paths.iter().map(String::as_str));
    if let Some(url) = &entry.web_url {
        parts.push(url);
    }
    normalize(&parts.join("\n"))
}

/// 질의의 모든 낱말(공백 구분)이 항목에 들어 있으면 참. 빈 질의는 모두 참.
pub fn matches_query(entry: &Entry, query: &str) -> bool {
    let tokens: Vec<String> = query.split_whitespace().map(normalize).collect();
    if tokens.is_empty() {
        return true;
    }
    let hay = haystack(entry);
    tokens.iter().all(|t| hay.contains(t.as_str()))
}

/// 분류·검색을 적용해 최신순으로 정렬한 항목의 위치(`entries` 인덱스)를 돌려준다.
pub fn filter_sorted(entries: &[Entry], category: Category, query: &str, is_dir: &dyn Fn(&str) -> Option<bool>) -> Vec<usize> {
    let mut hits: Vec<usize> = (0..entries.len())
        .filter(|&i| classify(&entries[i], is_dir).contains(category) && matches_query(&entries[i], query))
        .collect();
    hits.sort_by(|&a, &b| {
        entries[b].sort_time.partial_cmp(&entries[a].sort_time).unwrap_or(std::cmp::Ordering::Equal)
            .then(entries[b].id.cmp(&entries[a].id))
    });
    hits
}

#[cfg(test)]
mod tests {
    use super::*;

    fn none(_: &str) -> Option<bool> { None }
    fn text(source: &str, formats: &[&str], body: &str) -> Entry {
        Entry { kind: "text".into(), source: source.into(), formats: formats.iter().map(|s| s.to_string()).collect(),
                text: body.into(), preview: body.into(), ..Default::default() }
    }
    fn files(paths: &[&str]) -> Entry {
        Entry { kind: "files".into(), paths: paths.iter().map(|s| s.to_string()).collect(), ..Default::default() }
    }
    fn cats(e: &Entry, f: &dyn Fn(&str) -> Option<bool>) -> Vec<&'static str> {
        let s = classify(e, f);
        Category::ALL.iter().filter(|c| s.contains(**c)).map(|c| c.label()).collect()
    }

    #[test]
    fn plain_text_is_only_all() {
        assert_eq!(cats(&text("notepad.exe", &[], "안녕"), &none), ["전체"]);
    }

    #[test]
    fn document_by_source_and_format() {
        assert!(cats(&text("hwp.exe", &[], "x"), &none).contains(&"문서"));
        assert!(cats(&text("WINWORD.EXE", &[], "x"), &none).contains(&"문서"));
        assert!(cats(&text("unknown.exe", &["HWP Character Shape"], "x"), &none).contains(&"문서"));
        assert!(cats(&text("x.exe", &["Rich Text Format"], "x"), &none).contains(&"문서"));
    }

    #[test]
    fn browser_html_is_web_not_document() {
        let c = cats(&text("chrome.exe", &["HTML Format"], "표 내용"), &none);
        assert!(c.contains(&"웹") && !c.contains(&"문서"));
        assert!(!cats(&text("chrome.exe", &[], "그냥 글"), &none).contains(&"웹"));
    }

    #[test]
    fn web_by_url_text_marker_and_saved_url() {
        assert!(cats(&text("x.exe", &[], "https://example.com/a?b=1"), &none).contains(&"웹"));
        assert!(!cats(&text("x.exe", &[], "https://example.com 설명"), &none).contains(&"웹"));
        assert!(!cats(&text("x.exe", &[], "https://"), &none).contains(&"웹"));
        let mut e = text("excel.exe", &[], "셀");
        e.web_url = Some("https://a.com".into());
        assert!(cats(&e, &none).contains(&"웹"));
        let mut m = text("x.exe", &[], "q");
        m.preview = "본문 · 웹 · a.com".into();
        assert!(cats(&m, &none).contains(&"웹"));
    }

    #[test]
    fn image_and_capture() {
        let img = Entry { kind: "image".into(), preview: "그림 10×10".into(), source: "mspaint.exe".into(), ..Default::default() };
        assert_eq!(cats(&img, &none), ["전체", "그림"]);
        let cap = Entry { kind: "image".into(), preview: "캡처 · 그림 1×1".into(), source: "screenshot".into(), ..Default::default() };
        assert_eq!(cats(&cap, &none), ["전체", "그림", "화면캡처"]);
        let cap2 = Entry { kind: "image".into(), preview: "캡처 · 그림".into(), ..Default::default() };
        assert!(cats(&cap2, &none).contains(&"화면캡처"));
        let clip = Entry { kind: "image".into(), preview: "그림 5×5".into(), source: "ScreenClippingHost.exe".into(), ..Default::default() };
        assert!(cats(&clip, &none).contains(&"화면캡처"));
    }

    #[test]
    fn file_items_by_extension() {
        assert_eq!(cats(&files(&["C:\\a\\보고서.HWPX"]), &|_| Some(false)), ["전체", "문서", "파일"]);
        assert_eq!(cats(&files(&["C:\\a\\사진.JPG"]), &|_| Some(false)), ["전체", "그림", "파일"]);
        assert_eq!(cats(&files(&["C:\\a\\setup.exe"]), &|_| Some(false)), ["전체", "파일"]);
    }

    #[test]
    fn folder_vs_file_uses_injected_lookup() {
        let lookup = |p: &str| match p { "C:\\data" => Some(true), "C:\\x\\a.txt" => Some(false), _ => None };
        assert_eq!(cats(&files(&["C:\\data"]), &lookup), ["전체", "폴더"]);
        // 알려 준 값이 확장자 추정보다 우선
        assert_eq!(cats(&files(&["C:\\x\\a.txt"]), &lookup), ["전체", "문서", "파일"]);
        assert_eq!(cats(&files(&["C:\\data", "C:\\x\\a.txt"]), &lookup), ["전체", "문서", "파일", "폴더"]);
    }

    #[test]
    fn folder_guess_when_lookup_unknown() {
        assert!(cats(&files(&["C:\\Users\\kong\\Docs"]), &none).contains(&"폴더"));
        assert!(cats(&files(&["C:\\Users\\kong\\Docs\\"]), &none).contains(&"폴더"));
        assert!(cats(&files(&["D:"]), &none).contains(&"폴더"));
        assert!(cats(&files(&["/home/a/dir.v2/"]), &none).contains(&"폴더"));
        assert!(cats(&files(&["C:\\a\\.gitignore"]), &none).contains(&"폴더")); // 점 파일은 확장자 없음 → 추정은 폴더
        assert!(cats(&files(&["C:\\a\\b.tar.gz"]), &none).contains(&"파일"));
    }

    #[test]
    fn extension_edge_cases() {
        assert_eq!(extension("a.B.PDF"), Some("pdf".into()));
        assert_eq!(extension("C:\\a.b\\noext"), None);
        assert_eq!(extension("end."), None);
    }

    #[test]
    fn search_ignores_case_and_matches_hangul_composition() {
        let mut e = text("x.exe", &[], "Quarterly 한글 보고서");
        e.preview = e.text.clone();
        assert!(matches_query(&e, "quarterly"));
        assert!(matches_query(&e, "QUARTERLY 보고"));
        assert!(matches_query(&e, "한글"));
        assert!(matches_query(&e, "한ㄱ"));   // 조합 중
        assert!(matches_query(&e, "하"));     // 조합 중(알려진 과일치)
        assert!(!matches_query(&e, "ㅎㄱ")); // 초성 검색은 하지 않음(낱자 열이 이어져야 맞음)
        assert!(!matches_query(&e, "한글 없음"));
        assert!(matches_query(&e, "   "));
        // 분해형(NFD) 입력: ㅎ(1112)+ㅏ(1161)+ㄴ(11AB)
        assert!(matches_query(&e, "\u{1112}\u{1161}\u{11AB}\u{1100}\u{1173}\u{11AF}"));
    }

    #[test]
    fn search_covers_all_paths_and_url_but_not_source() {
        let mut e = files(&["C:\\a\\1.txt", "C:\\a\\2.txt", "C:\\a\\3.txt", "C:\\a\\넷째.pdf"]);
        e.preview = "파일 4개: 1.txt, 2.txt, 3.txt …".into();
        assert!(matches_query(&e, "넷째"));
        let mut w = text("chrome.exe", &[], "본문");
        w.web_url = Some("https://Example.com/x".into());
        assert!(matches_query(&w, "example.COM"));
        assert!(!matches_query(&w, "chrome"));
    }

    #[test]
    fn complex_vowels_and_finals_normalize_consistently() {
        assert_eq!(normalize("왜"), normalize("ㅇㅗㅐ"));
        assert_eq!(normalize("닭"), normalize("ㄷㅏㄹㄱ"));
        assert_eq!(normalize("ㄳ"), "ㄱㅅ");
    }

    #[test]
    fn filter_sorted_newest_first_with_id_tiebreak() {
        let mk = |id: i64, t: f64, src: &str| Entry { id, sort_time: t, kind: "text".into(), source: src.into(),
                                                       preview: format!("메모{id}"), ..Default::default() };
        let v = vec![mk(1, 10.0, "hwp.exe"), mk(2, 30.0, "x.exe"), mk(3, 30.0, "hwp.exe"), mk(4, 20.0, "hwp.exe")];
        assert_eq!(filter_sorted(&v, Category::All, "", &none), vec![2, 1, 3, 0]);
        assert_eq!(filter_sorted(&v, Category::Document, "", &none), vec![2, 3, 0]);
        assert_eq!(filter_sorted(&v, Category::Document, "메모4", &none), vec![3]);
        assert!(filter_sorted(&v, Category::Web, "", &none).is_empty());
    }
}
