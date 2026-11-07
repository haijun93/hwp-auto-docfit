//! 인코딩 감지·저장(UTF-8/BOM/UTF-16/CP949), 상태 표시줄 값, 범위 지정 모두 바꾸기.

use editor_core::api::Engine;
use editor_core::cp949;
use editor_core::doc::Document;
use editor_core::fileio::{self, Encoding, LineEnding};
use editor_core::search::SearchOpts;

fn hex(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn tmpdir(name: &str) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("editor_core_enc_{name}_{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

#[test]
fn cp949_table_matches_reference() {
    // 기준 값: Python 표준 코덱 cp949가 만든 (앞,뒤,유니코드) 전체를 FNV-1a(64)로 접은 값. 17,048자.
    let mut h: u64 = 0xcbf29ce484222325;
    let mut n = 0;
    for lead in 0x81u8..=0xFE {
        for trail in 0x41u8..=0xFE {
            if let Ok(s) = cp949::decode(&[lead, trail]) {
                let mut it = s.chars();
                let c = it.next().unwrap();
                assert!(it.next().is_none());
                for x in [lead as u64, trail as u64, c as u64] {
                    h = (h ^ x).wrapping_mul(0x100000001b3);
                }
                n += 1;
                // 왕복
                assert_eq!(cp949::encode(&s).unwrap(), vec![lead, trail], "{lead:02X}{trail:02X}");
            }
        }
    }
    assert_eq!(n, 17048);
    assert_eq!(cp949::MAPPED, 17048);
    assert_eq!(h, 0xf91a7e0ea3d1da1b);
}

#[test]
fn cp949_known_vectors() {
    for (ch, code) in [("가", "b0a1"), ("힣", "c652"), ("똠", "8c63"), ("뷁", "94ee"), ("갂", "8141"), ("한", "c7d1"), ("㉠", "a8b1"), ("①", "a8e7"), ("※", "a1d8"), ("一", "ece9"), ("ㄱ", "a4a1"), ("·", "a1a4"), ("€", "a2e6")] {
        assert_eq!(cp949::encode(ch).unwrap(), hex(code), "{ch}");
        assert_eq!(cp949::decode(&hex(code)).unwrap(), ch);
    }
    let s = "대한민국 헌법 제1조: 대한민국은 민주공화국이다. 漢字 ①";
    let b = hex("b4ebc7d1b9ceb1b920c7e5b9fd20c1a631c1b63a20b4ebc7d1b9ceb1b9c0ba20b9cec1d6b0f8c8adb1b9c0ccb4d92e20f9d3edae20a8e7");
    assert_eq!(cp949::encode(s).unwrap(), b);
    assert_eq!(cp949::decode(&b).unwrap(), s);
}

#[test]
fn cp949_rejects_bad_bytes_and_unmappable_chars() {
    assert_eq!(cp949::decode(&[0x41, 0x80]), Err(1)); // 0x80
    assert_eq!(cp949::decode(&[0xFF]), Err(0));
    assert_eq!(cp949::decode(&[0x41, 0xB0]), Err(1)); // 짝 없는 앞바이트
    assert_eq!(cp949::decode(&[0xB0, 0x20]), Err(0)); // 뒤바이트가 범위 밖
    assert_eq!(cp949::encode("a😀"), Err((1, '😀')));
    assert_eq!(cp949::encode("龥"), Err((0, '龥'))); // CP949에 없는 한자
    assert_eq!(cp949::first_unencodable("한글 ok"), None);
}

#[test]
fn detection_order_bom_utf8_cp949() {
    // 순수 ASCII → UTF-8
    assert_eq!(fileio::decode(b"hello\r\n").unwrap().1, Encoding::Utf8);
    // 한글 UTF-8 → UTF-8
    assert_eq!(fileio::decode("한글".as_bytes()).unwrap(), ("한글".to_string(), Encoding::Utf8));
    // BOM
    assert_eq!(fileio::decode(&fileio::encode("한글", Encoding::Utf8Bom).unwrap()).unwrap().1, Encoding::Utf8Bom);
    assert_eq!(fileio::decode(&fileio::encode("한글", Encoding::Utf16Le).unwrap()).unwrap().1, Encoding::Utf16Le);
    assert_eq!(fileio::decode(&fileio::encode("한글", Encoding::Utf16Be).unwrap()).unwrap().1, Encoding::Utf16Be);
    // BOM 없는 CP949 한글 → CP949
    let b = hex("c7d1b1db");
    assert_eq!(fileio::decode(&b).unwrap(), ("한글".to_string(), Encoding::Cp949));
    // 어느 쪽도 아님 → 오류(위치 안내)
    let e = fileio::decode(&[0x41, 0xFF, 0xFF]).unwrap_err();
    assert!(e.contains("UTF-8") && e.contains("CP949"), "{e}");
    // 이름·별칭
    for (n, e) in [("UTF-8", Encoding::Utf8), ("utf8", Encoding::Utf8), ("UTF-8 BOM", Encoding::Utf8Bom), ("utf-8-sig", Encoding::Utf8Bom), ("UTF-16 LE", Encoding::Utf16Le), ("utf-16be", Encoding::Utf16Be), ("CP949", Encoding::Cp949), ("EUC-KR", Encoding::Cp949), ("euc_kr", Encoding::Cp949), ("MS949", Encoding::Cp949)] {
        assert_eq!(Encoding::from_name(n), Some(e), "{n}");
    }
    assert_eq!(Encoding::from_name("latin1"), None);
    assert_eq!(Encoding::Cp949.name(), "CP949");
}

#[test]
fn forced_encoding_reopen() {
    // CP949 바이트를 UTF-8로 강제하면 오류, CP949로 강제하면 성공
    let b = hex("c7d1b1db");
    assert!(fileio::decode_as(&b, Encoding::Utf8).is_err());
    assert_eq!(fileio::decode_as(&b, Encoding::Cp949).unwrap(), "한글");
    // BOM 없는 UTF-16 LE도 지정하면 열린다
    let raw: Vec<u8> = "가a".encode_utf16().flat_map(|u| u.to_le_bytes()).collect();
    assert_eq!(fileio::decode_as(&raw, Encoding::Utf16Le).unwrap(), "가a");
    let d = Document::from_bytes_as(&b, Encoding::Cp949).unwrap();
    assert_eq!(d.encoding, Encoding::Cp949);
}

#[test]
fn cp949_file_roundtrip_keeps_encoding_and_line_endings() {
    let dir = tmpdir("rt");
    let p = dir.join("old.txt");
    // CP949 + CRLF 로 만든 옛 파일
    let src = "제목\r\n대한민국 ①\r\n끝";
    std::fs::write(&p, cp949::encode(src).unwrap()).unwrap();
    let mut d = Document::open(&p).unwrap();
    assert_eq!((d.encoding, d.line_ending), (Encoding::Cp949, LineEnding::Crlf));
    assert_eq!(d.text(), "제목\n대한민국 ①\n끝");
    d.insert(0, "새 ").unwrap();
    d.save(&p).unwrap();
    let on_disk = std::fs::read(&p).unwrap();
    assert_eq!(on_disk, cp949::encode("새 제목\r\n대한민국 ①\r\n끝").unwrap());
    // 다른 인코딩으로 저장(UTF-8 기본으로 바꿔 저장)
    d.set_encoding(Encoding::Utf8).unwrap();
    d.save(&dir.join("new.txt")).unwrap();
    assert_eq!(std::fs::read(dir.join("new.txt")).unwrap(), "새 제목\r\n대한민국 ①\r\n끝".as_bytes());
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn new_document_defaults_to_utf8() {
    let d = Document::new();
    assert_eq!(d.encoding, Encoding::Utf8);
    let d = Document::from_text("가나");
    assert_eq!(d.encoding, Encoding::Utf8);
}

#[test]
fn unencodable_text_blocks_cp949_and_never_corrupts() {
    let dir = tmpdir("bad");
    let p = dir.join("a.txt");
    let mut d = Document::from_text("가\n😀 이모지\n");
    // 바꾸기 전에 거절하고 위치를 알린다
    let e = d.set_encoding(Encoding::Cp949).unwrap_err();
    assert!(e.contains("😀") && e.contains("2줄 1열"), "{e}");
    assert_eq!(d.encoding, Encoding::Utf8);
    // 이미 CP949인 문서에 이모지를 입력하면 저장이 거절되고 원본 파일은 그대로
    let mut d2 = Document::from_text("가");
    d2.set_encoding(Encoding::Cp949).unwrap();
    d2.save(&p).unwrap();
    let before = std::fs::read(&p).unwrap();
    d2.insert(3, "😀").unwrap();
    assert!(d2.save(&p).unwrap_err().contains("CP949"));
    assert!(d2.is_dirty());
    assert_eq!(std::fs::read(&p).unwrap(), before);
    assert!(d2.autosave(&dir.join("rec")).is_err());
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn status_values() {
    let mut d = Document::from_bytes("가나다\r\n😀ab\r\n\r\n끝".as_bytes()).unwrap();
    // 내부 텍스트: "가나다\n😀ab\n\n끝"
    let t = d.text().to_string();
    assert_eq!(t, "가나다\n😀ab\n\n끝");
    let pos_b = t.find('b').unwrap();
    let s = d.status(pos_b, None).unwrap();
    assert_eq!((s.line, s.col), (2, 3)); // 😀(1) a(2) b(3): b 앞의 열은 3
    assert_eq!(s.lines, 4);
    assert_eq!(s.chars, 3 + 1 + 3 + 1 + 1 + 1); // 가나다 \n 😀ab \n \n 끝 = 10
    assert_eq!(s.chars_no_newline, 7);
    assert_eq!(s.line_ending, LineEnding::Crlf);
    assert_eq!(s.encoding, Encoding::Utf8);
    assert_eq!(s.selected_chars, None);
    // 선택 영역: 가나다\n 까지 = 4글자
    let s = d.status(0, Some((0, "가나다\n".len()))).unwrap();
    assert_eq!((s.line, s.col, s.selected_chars), (1, 1, Some(4)));
    // 문서 끝
    let s = d.status(d.len(), None).unwrap();
    assert_eq!((s.line, s.col), (4, 2));
    // 글자 경계가 아니면 오류
    assert!(d.status(1, None).is_err());
}

#[test]
fn status_api_summary_and_cp949_open() {
    let dir = tmpdir("api");
    let p = dir.join("k.txt");
    std::fs::write(&p, cp949::encode("한글\r\n메모").unwrap()).unwrap();
    let mut e = Engine::new();
    let r = e.handle(&format!(r#"{{"cmd":"edit_open","path":{:?}}}"#, p.to_string_lossy()));
    assert!(r.contains(r#""encoding":"CP949""#) && r.contains(r#""line_ending":"CRLF""#), "{r}");
    let r = e.handle(r#"{"cmd":"edit_status","doc":1,"pos":7,"sel_start":0,"sel_end":3}"#);
    assert!(r.contains(r#""line":2"#) && r.contains(r#""col":1"#), "{r}");
    assert!(r.contains(r#""selected_chars":1"#) && r.contains(r#""chars":5"#), "{r}");
    assert!(r.contains("줄 2, 열 1") && r.contains("Windows (CRLF)") && r.contains("CP949"), "{r}");
    // 인코딩 지정 다시 열기와 변경
    let r = e.handle(&format!(r#"{{"cmd":"edit_open","path":{:?},"encoding":"UTF-8"}}"#, p.to_string_lossy()));
    assert!(r.contains(r#""ok":false"#), "{r}");
    let r = e.handle(&format!(r#"{{"cmd":"edit_open","path":{:?},"encoding":"EUC-KR"}}"#, p.to_string_lossy()));
    assert!(r.contains(r#""ok":true"#) && r.contains(r#""encoding":"CP949""#), "{r}");
    let r = e.handle(r#"{"cmd":"edit_set_encoding","doc":1,"encoding":"UTF-16 LE"}"#);
    assert!(r.contains(r#""encoding":"UTF-16 LE""#), "{r}");
    let r = e.handle(r#"{"cmd":"edit_set_encoding","doc":1,"encoding":"latin1"}"#);
    assert!(r.contains(r#""ok":false"#) && r.contains("CP949"), "{r}");
    let _ = std::fs::remove_dir_all(&dir);
}

// ---------- 찾기·바꾸기 고급 ----------

const CS: SearchOpts = SearchOpts { case_sensitive: true, whole_word: false };
const CI: SearchOpts = SearchOpts { case_sensitive: false, whole_word: false };

#[test]
fn replace_all_is_single_undo_unit_with_dirty_tracking() {
    let mut d = Document::from_text("a b a b a\nb a");
    d.mark_clean();
    assert!(!d.is_dirty());
    let r = d.replace_all_in("a", "XYZ", CS, None).unwrap();
    assert_eq!(r.count, 4);
    assert_eq!(d.text(), "XYZ b XYZ b XYZ\nb XYZ");
    assert!(d.is_dirty());
    assert_eq!(r.range, Some((0, "XYZ b XYZ b XYZ\nb XYZ".len())));
    d.undo().unwrap(); // 한 번에 전부
    assert_eq!(d.text(), "a b a b a\nb a");
    assert!(!d.is_dirty());
    assert!(!d.can_undo());
    d.redo().unwrap();
    assert_eq!(d.text(), "XYZ b XYZ b XYZ\nb XYZ");
}

#[test]
fn replace_all_within_selection_and_word_boundaries() {
    // 선택 영역 안만 바꾼다
    let mut d = Document::from_text("cat cat cat cat");
    let r = d.replace_all_in("cat", "dog", CS, Some((4, 11))).unwrap();
    assert_eq!(r.count, 2);
    assert_eq!(d.text(), "cat dog dog cat");
    assert_eq!(r.range, Some((4, 11)));
    d.undo().unwrap();
    assert_eq!(d.text(), "cat cat cat cat");
    // 범위 가장자리에 걸친 일치는 제외
    let r = d.replace_all_in("cat", "dog", CS, Some((5, 11))).unwrap();
    assert_eq!(r.count, 1);
    assert_eq!(d.text(), "cat cat dog cat");
    // 온전한 낱말: 범위 밖 글자도 본다 (선택이 'cat'의 일부만 덮으면 낱말이 아님)
    let mut d = Document::from_text("concat cat");
    let ww = SearchOpts { case_sensitive: true, whole_word: true };
    assert_eq!(d.replace_all_in("cat", "X", ww, Some((3, 10))).unwrap().count, 1);
    assert_eq!(d.text(), "concat X");
    // 잘못된 범위
    assert!(d.replace_all_in("a", "b", CS, Some((5, 99))).is_err());
}

#[test]
fn replace_all_edge_cases() {
    // 없으면 아무 일도 없다(실행취소 항목 없음)
    let mut d = Document::from_text("abc");
    d.mark_clean();
    let r = d.replace_all_in("zzz", "y", CS, None).unwrap();
    assert_eq!((r.count, r.range), (0, None));
    assert!(!d.can_undo() && !d.is_dirty());
    // 빈 검색어
    assert_eq!(d.replace_all("", "x", CS).unwrap(), 0);
    // 같은 말로 바꾸면 글이 안 바뀌므로 기록·dirty 없음(개수는 알려 준다)
    let r = d.replace_all_in("b", "b", CS, None).unwrap();
    assert_eq!(r.count, 1);
    assert!(!d.can_undo() && !d.is_dirty());
    // 바꿀 말에 찾는 말이 들어 있어도 무한히 늘지 않는다
    let mut d = Document::from_text("aaa");
    assert_eq!(d.replace_all("a", "aa", CS).unwrap(), 3);
    assert_eq!(d.text(), "aaaaaa");
    // 지우기(빈 바꿀 말)
    let mut d = Document::from_text("a-b-c");
    assert_eq!(d.replace_all("-", "", CS).unwrap(), 2);
    assert_eq!(d.text(), "abc");
    d.undo().unwrap();
    assert_eq!(d.text(), "a-b-c");
    // 대소문자 무시 + 한글
    let mut d = Document::from_text("Hello HELLO hello 안녕");
    assert_eq!(d.replace_all("hello", "하이", CI).unwrap(), 3);
    assert_eq!(d.text(), "하이 하이 하이 안녕");
    // 여러 줄 찾는 말: 입력 칸의 CRLF도 LF 글과 일치, 바꿀 말의 CRLF는 LF로
    let mut d = Document::from_bytes("a\r\nb\r\nc".as_bytes()).unwrap();
    assert_eq!(d.replace_all("a\r\nb", "x\r\ny", CS).unwrap(), 1);
    assert_eq!(d.text(), "x\ny\nc");
    assert_eq!(d.to_bytes().unwrap(), b"x\r\ny\r\nc");
    // 사용자가 연 묶음 안에서는 그 묶음에 합쳐진다
    let mut d = Document::from_text("a a");
    d.begin_group();
    d.insert(0, "Q").unwrap();
    d.replace_all("a", "b", CS).unwrap();
    d.end_group();
    d.undo().unwrap();
    assert_eq!(d.text(), "a a");
}

#[test]
fn replace_all_api_scope_and_selection_result() {
    let mut e = Engine::new();
    e.handle(r#"{"cmd":"edit_open","text":"cat cat cat"}"#);
    let r = e.handle(r#"{"cmd":"edit_find_all","doc":1,"query":"cat","start":4,"end":11}"#);
    assert!(r.contains(r#""count":2"#), "{r}");
    let r = e.handle(r#"{"cmd":"edit_replace_all","doc":1,"query":"cat","with":"horse","start":4,"end":11,"case_sensitive":true}"#);
    assert!(r.contains(r#""count":2"#) && r.contains(r#""sel_start":4"#) && r.contains(r#""sel_end":15"#) && r.contains(r#""can_undo":true"#), "{r}");
    let r = e.handle(r#"{"cmd":"edit_undo","doc":1}"#);
    assert!(r.contains(r#""can_undo":false"#), "{r}");
    assert!(e.handle(r#"{"cmd":"edit_replace_all","doc":1,"query":"cat","start":3}"#).contains(r#""ok":false"#));
}
