use editor_core::api::Engine;
use editor_core::doc::Document;
use editor_core::fileio::{self, Encoding, LineEnding};
use editor_core::json::{self, Json};
use editor_core::markdown::{self, BlockKind, BlockSet, Inline, SpanKind};
use editor_core::search::SearchOpts;

const CI: SearchOpts = SearchOpts { case_sensitive: false, whole_word: false };
const CS: SearchOpts = SearchOpts { case_sensitive: true, whole_word: false };

fn tmpdir(name: &str) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("editor_core_test_{}_{name}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

// ---------- 버퍼·한글 ----------

#[test]
fn hangul_composition_steps_become_one_undo() {
    let mut d = Document::new();
    // IME가 조합 구간을 매번 교체하는 순서: ㅎ → 하 → 한 → (확정 후) ㄱ → 그 → 글
    d.insert(0, "ㅎ").unwrap();
    d.replace_range(0, 3, "하").unwrap();
    d.replace_range(0, 3, "한").unwrap();
    d.insert(3, "ㄱ").unwrap();
    d.replace_range(3, 6, "그").unwrap();
    d.replace_range(3, 6, "글").unwrap();
    assert_eq!(d.text(), "한글");
    assert_eq!(d.len(), 6);
    assert_eq!(d.stats().chars, 2);
    assert!(d.undo().is_some());
    assert_eq!(d.text(), "");
    assert!(d.redo().is_some());
    assert_eq!(d.text(), "한글");
}

#[test]
fn rejects_non_char_boundary_and_out_of_range() {
    let mut d = Document::from_text("한글");
    assert!(d.insert(1, "x").is_err());
    assert!(d.delete(0, 2).is_err());
    assert!(d.insert(7, "x").is_err());
    assert!(d.slice(3, 1).is_err());
    assert_eq!(d.text(), "한글");
}

#[test]
fn line_col_counts_chars_and_utf16() {
    let mut d = Document::from_text("가나\n다라😀마\n");
    assert_eq!(d.stats().lines, 3);
    assert_eq!(d.line_col(0).unwrap(), (1, 1));
    assert_eq!(d.line_col(6).unwrap(), (1, 3)); // 줄 끝
    let after_emoji = 7 + 6 + 4; // "가나\n"(7) + "다라"(6) + 😀(4)
    assert_eq!(d.line_col(after_emoji).unwrap(), (2, 4));
    assert_eq!(d.offset_of(2, 4), after_emoji);
    assert_eq!(d.offset_of(2, 99), 7 + 6 + 4 + 3); // 줄 끝으로 맞춤
    assert_eq!(d.byte_to_utf16(after_emoji).unwrap(), 7); // 가나\n다라(5) + 😀(2)
    assert_eq!(d.utf16_to_byte(7).unwrap(), after_emoji);
    assert!(d.utf16_to_byte(6).is_err()); // 대리 쌍 한가운데
}

#[test]
fn utf8_boundaries_random_model() {
    // 간단한 선형 합동 난수로 String 모델과 비교(삽입·삭제·실행취소 전부 되돌리기)
    let pieces = ["a", "한", "글", "😀", "
", " ", "é", "漢", "\n\n"];
    let mut seed = 12345u64;
    let mut rnd = move |n: usize| {
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((seed >> 33) as usize) % n
    };
    let mut d = Document::new();
    let mut model = String::new();
    let mut snapshots = vec![String::new()];
    for _ in 0..3000 {
        let boundaries: Vec<usize> = model.char_indices().map(|(i, _)| i).chain([model.len()]).collect();
        let a = boundaries[rnd(boundaries.len())];
        let b = boundaries[rnd(boundaries.len())];
        let (s, e) = (a.min(b), a.max(b));
        let ins = if rnd(3) == 0 { "" } else { pieces[rnd(pieces.len())] };
        d.commit();
        d.replace_range(s, e, ins).unwrap();
        model.replace_range(s..e, ins);
        if !(s == e && ins.is_empty()) {
            snapshots.push(model.clone());
        }
        assert_eq!(d.text(), model);
        assert_eq!(d.stats().chars, model.chars().count());
        assert_eq!(d.line_count(), model.matches('\n').count() + 1);
    }
    // 줄 색인 검증
    for l in 0..d.line_count() {
        let expect: Vec<&str> = model.split('\n').collect();
        assert_eq!(d.line_text(l), expect[l]);
    }
    // 끝까지 실행취소하면 단계별로 스냅샷과 같다
    let mut i = snapshots.len() - 1;
    while d.undo().is_some() {
        i -= 1;
        assert_eq!(d.text(), snapshots[i]);
    }
    assert_eq!(d.text(), "");
    while d.redo().is_some() {}
    assert_eq!(d.text(), *snapshots.last().unwrap());
}

// ---------- 실행취소 ----------

#[test]
fn typing_groups_by_word_and_newline() {
    let mut d = Document::new();
    for (i, c) in "hello".chars().enumerate() {
        d.insert(i, &c.to_string()).unwrap();
    }
    for (i, c) in " world".chars().enumerate() {
        d.insert(5 + i, &c.to_string()).unwrap();
    }
    d.insert(11, "\n").unwrap();
    d.insert(12, "x").unwrap();
    assert_eq!(d.text(), "hello world\nx");
    d.undo(); // 줄바꿈부터 이어 쓴 글이 한 묶음
    assert_eq!(d.text(), "hello world");
    d.undo();
    assert_eq!(d.text(), "hello");
    d.undo();
    assert_eq!(d.text(), "");
    assert!(d.undo().is_none());
}

#[test]
fn explicit_group_redo_and_dirty() {
    let mut d = Document::from_text("abc");
    assert!(!d.is_dirty());
    d.begin_group();
    d.insert(3, "d").unwrap();
    d.insert(0, "Z").unwrap();
    d.end_group();
    assert!(d.is_dirty());
    assert_eq!(d.text(), "Zabcd");
    d.undo();
    assert_eq!(d.text(), "abc");
    assert!(!d.is_dirty());
    d.redo();
    assert_eq!(d.text(), "Zabcd");
    assert!(d.is_dirty());
    d.undo();
    d.insert(0, "Q").unwrap(); // 새 편집은 다시실행 기록을 지운다
    assert!(!d.can_redo());
    assert!(d.is_dirty());
}

#[test]
fn backspace_and_delete_runs_merge() {
    let mut d = Document::from_text("abcdef");
    d.delete(5, 6).unwrap();
    d.delete(4, 5).unwrap();
    d.delete(3, 4).unwrap();
    assert_eq!(d.text(), "abc");
    d.undo();
    assert_eq!(d.text(), "abcdef");
    d.delete(0, 1).unwrap();
    d.delete(0, 1).unwrap(); // Delete 키 연속
    assert_eq!(d.text(), "cdef");
    d.undo();
    assert_eq!(d.text(), "abcdef");
}

#[test]
fn undo_depth_is_many_steps() {
    let mut d = Document::new();
    for i in 0..300 {
        d.commit();
        d.insert(d.len(), &format!("{i},")).unwrap();
    }
    let mut n = 0;
    while d.undo().is_some() {
        n += 1;
    }
    assert_eq!(n, 300);
    assert_eq!(d.text(), "");
}

// ---------- 찾기·바꾸기 ----------

#[test]
fn find_case_options_and_hangul() {
    let mut d = Document::from_text("Hello hello HELLO 한글 한글날 Élan élan");
    assert_eq!(d.find_all("hello", CI, 100).len(), 3);
    assert_eq!(d.find_all("hello", CS, 100).len(), 1);
    assert_eq!(d.find_all("élan", CI, 100).len(), 2);
    assert_eq!(d.find_all("한글", CS, 100).len(), 2);
    let ww = SearchOpts { case_sensitive: true, whole_word: true };
    assert_eq!(d.find_all("한글", ww, 100).len(), 1);
    let (s, e) = d.find_next("한글", 0, CS, false).unwrap();
    assert_eq!(&d.text()[s..e], "한글");
    // 끝에서 처음으로 돌아가기
    let total = d.len();
    assert!(d.find_next("Hello", total, CS, false).is_none());
    assert_eq!(d.find_next("Hello", total, CS, true), Some((0, 5)));
}

#[test]
fn replace_all_is_one_undo_and_counts() {
    let mut d = Document::from_text("aa Aa aA a\nA");
    assert_eq!(d.replace_all("a", "한", CI).unwrap(), 8);
    assert_eq!(d.text(), "한한 한한 한한 한\n한");
    d.undo();
    assert_eq!(d.text(), "aa Aa aA a\nA");
    assert_eq!(d.replace_all("a", "-", CS).unwrap(), 5);
    assert_eq!(d.text(), "-- A- -A -\nA");
    assert_eq!(d.replace_all("zzz", "x", CS).unwrap(), 0);
    let r = d.replace_next("A", "BB", 0, CS, true).unwrap();
    assert_eq!(r, Some((3, 5)));
    assert_eq!(d.text(), "-- BB- -A -\nA");
}

// ---------- Markdown ----------

fn blocks(text: &str) -> Vec<markdown::Block> {
    let d = Document::from_text(text);
    markdown::parse(&d, 0, d.line_count())
}

#[test]
fn markdown_block_kinds() {
    let src = "# 제목\n## 둘\n\n본문 **굵게**\n- 가\n  - 나\n* 다\n1. 하나\n12. 열둘\n> 인용\n---\n***\n```rust\nlet x = **1**;\n```\n끝";
    let b = blocks(src);
    let k: Vec<_> = b.iter().map(|x| x.kind.clone()).collect();
    assert_eq!(k[0], BlockKind::Heading(1));
    assert_eq!(k[1], BlockKind::Heading(2));
    assert_eq!(k[2], BlockKind::Blank);
    assert_eq!(k[3], BlockKind::Paragraph);
    assert_eq!(k[4], BlockKind::Bullet { indent: 0 });
    assert_eq!(k[5], BlockKind::Bullet { indent: 1 });
    assert_eq!(k[6], BlockKind::Bullet { indent: 0 });
    assert_eq!(k[7], BlockKind::Number { n: 1, indent: 0 });
    assert_eq!(k[8], BlockKind::Number { n: 12, indent: 0 });
    assert_eq!(k[9], BlockKind::Quote);
    assert_eq!(k[10], BlockKind::Rule);
    assert_eq!(k[11], BlockKind::Rule);
    assert_eq!(k[12], BlockKind::Fence { lang: "rust".into(), open: true });
    assert_eq!(k[13], BlockKind::Code);
    assert_eq!(k[14], BlockKind::Fence { lang: String::new(), open: false });
    assert_eq!(k[15], BlockKind::Paragraph);
    assert!(b[13].spans.is_empty(), "코드 블록 안은 인라인 해석 안 함");
    assert_eq!(&src[b[0].content_start..b[0].end], "제목");
    // '#태그'는 제목이 아니다
    assert_eq!(blocks("#태그")[0].kind, BlockKind::Paragraph);
}

#[test]
fn markdown_inline_spans() {
    let src = "가 **굵게** 와 *기울임* 그리고 `a*b` 와 [링크](http://x.kr/a_b) snake_case_name";
    let d = Document::from_text(src);
    let sp = &markdown::parse(&d, 0, 1)[0].spans;
    let text = |a: usize, b: usize| src[a..b].to_string();
    let kinds: Vec<_> = sp.iter().map(|s| s.kind).collect();
    assert_eq!(kinds, vec![SpanKind::Bold, SpanKind::Italic, SpanKind::Code, SpanKind::Link]);
    assert_eq!(text(sp[0].content_start, sp[0].content_end), "굵게");
    assert_eq!(text(sp[1].content_start, sp[1].content_end), "기울임");
    assert_eq!(text(sp[2].content_start, sp[2].content_end), "a*b");
    assert_eq!(text(sp[3].content_start, sp[3].content_end), "링크");
    let (u0, u1) = sp[3].url.unwrap();
    assert_eq!(text(u0, u1), "http://x.kr/a_b");
    // 굵게+기울임 중첩
    let d = Document::from_text("***둘다*** 와 **굵은 *안* 글**");
    let sp = &markdown::parse(&d, 0, 1)[0].spans;
    assert_eq!(sp.iter().filter(|s| s.kind == SpanKind::Bold).count(), 2);
    assert_eq!(sp.iter().filter(|s| s.kind == SpanKind::Italic).count(), 2);
    // 닫히지 않으면 글자 그대로
    let d = Document::from_text("2 * 3 = 6 그리고 **열림");
    assert!(markdown::parse(&d, 0, 1)[0].spans.is_empty());
}

#[test]
fn toggle_inline_wraps_and_unwraps() {
    let mut d = Document::from_text("가나다 라마");
    let (a, b) = markdown::toggle_inline(&mut d, 0, 9, Inline::Bold).unwrap();
    assert_eq!(d.text(), "**가나다** 라마");
    assert_eq!(&d.text()[a..b], "가나다");
    // 같은 선택으로 다시 → 해제
    let (a, b) = markdown::toggle_inline(&mut d, a, b, Inline::Bold).unwrap();
    assert_eq!(d.text(), "가나다 라마");
    assert_eq!((a, b), (0, 9));
    // 표지까지 포함해 선택해도 해제
    markdown::toggle_inline(&mut d, 0, 9, Inline::Italic).unwrap();
    assert_eq!(d.text(), "*가나다* 라마");
    markdown::toggle_inline(&mut d, 0, 11, Inline::Italic).unwrap();
    assert_eq!(d.text(), "가나다 라마");
    // 굵게 위에 기울임 → 세 개, 기울임만 해제 → 굵게 유지
    markdown::toggle_inline(&mut d, 0, 9, Inline::Bold).unwrap();
    markdown::toggle_inline(&mut d, 2, 11, Inline::Italic).unwrap();
    assert_eq!(d.text(), "***가나다*** 라마");
    markdown::toggle_inline(&mut d, 3, 12, Inline::Italic).unwrap();
    assert_eq!(d.text(), "**가나다** 라마");
    // 선택 없음 → 빈 표지 쌍, 커서는 가운데
    let mut e = Document::from_text("x");
    let (a, b) = markdown::toggle_inline(&mut e, 1, 1, Inline::Code).unwrap();
    assert_eq!((e.text(), a, b), ("x``", 2, 2));
    // 한 번의 실행취소로 원복
    d.undo();
    assert_ne!(d.text(), "**가나다** 라마");
}

#[test]
fn set_block_toggles_and_numbers() {
    let mut d = Document::from_text("하나\n둘\n셋");
    let n = d.len();
    markdown::set_block(&mut d, 0, n, BlockSet::Bullet).unwrap();
    assert_eq!(d.text(), "- 하나\n- 둘\n- 셋");
    let n = d.len();
    markdown::set_block(&mut d, 0, n, BlockSet::Number).unwrap();
    assert_eq!(d.text(), "1. 하나\n2. 둘\n3. 셋");
    let n = d.len();
    markdown::set_block(&mut d, 0, n, BlockSet::Number).unwrap(); // 이미 번호 → 보통으로
    assert_eq!(d.text(), "하나\n둘\n셋");
    markdown::set_block(&mut d, 0, 0, BlockSet::Heading(2)).unwrap();
    assert_eq!(d.text(), "## 하나\n둘\n셋");
    markdown::set_block(&mut d, 0, 0, BlockSet::Heading(3)).unwrap(); // 제목 단계 바꾸기
    assert_eq!(d.text(), "### 하나\n둘\n셋");
    let n = d.len();
    markdown::set_block(&mut d, 0, n, BlockSet::Quote).unwrap();
    assert_eq!(d.text(), "> 하나\n> 둘\n> 셋");
    d.undo();
    assert_eq!(d.text(), "### 하나\n둘\n셋");
}

#[test]
fn set_block_skips_code_blocks() {
    let mut d = Document::from_text("a\n```\ncode\n```\nb");
    let n = d.len();
    markdown::set_block(&mut d, 0, n, BlockSet::Quote).unwrap();
    assert_eq!(d.text(), "> a\n```\ncode\n```\n> b");
}

#[test]
fn link_rule_code_block_and_clear() {
    let mut d = Document::from_text("본문 주소");
    let (a, b) = markdown::insert_link(&mut d, 7, 13, "http://a.kr").unwrap();
    assert_eq!(d.text(), "본문 [주소](http://a.kr)");
    assert_eq!(&d.text()[a..b], "주소");

    let mut r = Document::from_text("앞\n뒤");
    let c = markdown::insert_rule(&mut r, 3).unwrap();
    assert_eq!(r.text(), "앞\n---\n\n뒤");
    assert_eq!(c, "앞\n---\n".len());

    let mut c = Document::from_text("x\ny");
    let n = c.len();
    markdown::toggle_code_block(&mut c, 0, n).unwrap();
    assert_eq!(c.text(), "```\nx\ny\n```");
    let n = c.len();
    markdown::toggle_code_block(&mut c, 0, n).unwrap();
    assert_eq!(c.text(), "x\ny");

    let mut f = Document::from_text("# **제목** 과 *기울*\n- `코드` [링크](u)\n> 인용\n```\nkeep **me**\n```");
    let n = f.len();
    markdown::clear_format(&mut f, 0, n).unwrap();
    assert_eq!(f.text(), "제목 과 기울\n코드 링크\n인용\nkeep **me**");
    f.undo();
    assert!(f.text().starts_with("# **제목**"));
}

// ---------- 줄바꿈·인코딩·저장 ----------

#[test]
fn line_ending_detection_and_roundtrip() {
    assert_eq!(fileio::detect_line_ending("a\r\nb\r\nc"), (LineEnding::Crlf, false));
    assert_eq!(fileio::detect_line_ending("a\nb\nc"), (LineEnding::Lf, false));
    assert_eq!(fileio::detect_line_ending("a\rb"), (LineEnding::Cr, false));
    assert_eq!(fileio::detect_line_ending("a\r\nb\nc\n"), (LineEnding::Lf, true));
    assert_eq!(fileio::detect_line_ending("한줄"), (LineEnding::Lf, false));
    let mut d = Document::from_bytes("가\r\n나\r\n다".as_bytes()).unwrap();
    assert_eq!(d.line_ending, LineEnding::Crlf);
    assert_eq!(d.text(), "가\n나\n다");
    assert_eq!(d.to_bytes(), "가\r\n나\r\n다".as_bytes());
    d.line_ending = LineEnding::Lf;
    assert_eq!(d.to_bytes(), "가\n나\n다".as_bytes());
    // 붙여넣은 CRLF도 내부는 LF
    d.insert(0, "x\r\ny\rz").unwrap();
    assert!(!d.text().contains('\r'));
}

#[test]
fn encodings_roundtrip() {
    for enc in [Encoding::Utf8, Encoding::Utf8Bom, Encoding::Utf16Le, Encoding::Utf16Be] {
        let bytes = fileio::encode("한글😀abc", enc);
        let (s, e) = fileio::decode(&bytes).unwrap();
        assert_eq!((s.as_str(), e), ("한글😀abc", enc));
    }
    assert!(fileio::decode(&[0xB0, 0xA1, 0xB3, 0xAA]).is_err()); // CP949 "가나"
    let d = Document::from_bytes(&fileio::encode("가\r\n나", Encoding::Utf16Le)).unwrap();
    assert_eq!((d.encoding, d.line_ending), (Encoding::Utf16Le, LineEnding::Crlf));
}

#[test]
fn atomic_save_and_autosave() {
    let dir = tmpdir("save");
    let path = dir.join("메모.txt");
    std::fs::write(&path, "원본").unwrap();
    let mut d = Document::open(&path).unwrap();
    d.insert(d.len(), " 추가\n둘째").unwrap();
    assert!(d.is_dirty());
    let rec = dir.join("복구").join("메모.autosave");
    d.autosave(&rec).unwrap();
    assert!(d.is_dirty(), "자동 저장은 변경 상태를 바꾸지 않는다");
    assert_eq!(std::fs::read(&rec).unwrap(), "원본 추가\r\n둘째".as_bytes());
    d.save(&path).unwrap();
    assert!(!d.is_dirty());
    assert_eq!(std::fs::read_to_string(&path).unwrap(), "원본 추가\r\n둘째");
    let leftovers: Vec<_> = std::fs::read_dir(&dir).unwrap().filter_map(|e| e.ok()).filter(|e| e.file_name().to_string_lossy().ends_with(".tmp")).collect();
    assert!(leftovers.is_empty());
    std::fs::remove_dir_all(&dir).unwrap();
}

// ---------- JSON·API ----------

#[test]
fn json_roundtrip_and_errors() {
    let v = json::parse(r#"{"a":[1,2.5,-3e2,true,null,"\u00e9\ud83d\ude00\n\"x"],"한":{"b":""}}"#).unwrap();
    let s = json::to_string(&v);
    assert_eq!(json::parse(&s).unwrap(), v);
    assert_eq!(v.get("a"), json::parse(r#"[1,2.5,-300,true,null,"é😀\n\"x"]"#).ok().as_ref());
    assert!(json::parse("{\"a\":").is_err());
    assert!(json::parse("[1,]").is_err());
    assert!(json::parse("\"\\ud83d\"").is_err());
    assert!(json::parse("{} x").is_err());
    assert_eq!(json::to_string(&Json::Str("\u{1}\t".into())), "\"\\u0001\\t\"");
}

fn call(e: &mut Engine, req: &str) -> Json {
    json::parse(&e.handle(req)).unwrap()
}

#[test]
fn api_session_flow() {
    let mut e = Engine::new();
    let r = call(&mut e, r#"{"cmd":"edit_open","text":"가나다\r\n라마"}"#);
    assert_eq!(r.bool("ok"), Some(true));
    assert_eq!(r.str("line_ending"), Some("CRLF"));
    let doc = r.usize("doc").unwrap();
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_insert","doc":{doc},"pos":9,"text":"!"}}"#));
    assert_eq!(r.usize("cursor"), Some(10));
    assert_eq!(r.bool("dirty"), Some(true));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_text","doc":{doc}}}"#));
    assert_eq!(r.str("text"), Some("가나다!\n라마"));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_find_all","doc":{doc},"query":"다"}}"#));
    assert_eq!(r.usize("count"), Some(1));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_md_inline","doc":{doc},"start":0,"end":9,"kind":"bold"}}"#));
    assert_eq!((r.usize("sel_start"), r.usize("sel_end")), (Some(2), Some(11)));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_md_parse","doc":{doc}}}"#));
    let Some(Json::Arr(bl)) = r.get("blocks") else { panic!() };
    assert_eq!(bl.len(), 2);
    assert_eq!(bl[0].str("kind"), Some("paragraph"));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_undo","doc":{doc}}}"#));
    assert_eq!(r.bool("changed"), Some(true));
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_line_col","doc":{doc},"pos":11}}"#));
    assert_eq!((r.usize("line"), r.usize("col")), (Some(2), Some(1)));
    // 오류 응답
    let r = call(&mut e, &format!(r#"{{"cmd":"edit_insert","doc":{doc},"pos":1,"text":"x"}}"#));
    assert_eq!(r.bool("ok"), Some(false));
    assert!(r.str("message").unwrap().contains("글자 경계"));
    let r = call(&mut e, r#"{"cmd":"edit_nope"}"#);
    assert_eq!(r.bool("ok"), Some(false));
    let r = call(&mut e, "not json");
    assert_eq!(r.bool("ok"), Some(false));
    assert_eq!(call(&mut e, &format!(r#"{{"cmd":"edit_close","doc":{doc}}}"#)).bool("ok"), Some(true));
    assert_eq!(call(&mut e, &format!(r#"{{"cmd":"edit_text","doc":{doc}}}"#)).bool("ok"), Some(false));
}
