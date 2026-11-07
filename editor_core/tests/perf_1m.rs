//! 100만 글자 삽입·삭제·실행취소 측정. `cargo test --release --test perf_1m -- --nocapture`
//! 디버그 빌드에서는 10만 글자로 줄여 통과 여부만 본다(숫자는 release 기준으로 docs에 기록).
//! 출력 줄은 `ROW|배치|항목|ms|비고` 형식이라 표로 옮기기 쉽다.

use editor_core::doc::Document;
use editor_core::search::SearchOpts;
use std::time::Instant;

const N: usize = if cfg!(debug_assertions) { 100_000 } else { 1_000_000 };

fn ms(t: Instant) -> f64 {
    t.elapsed().as_secs_f64() * 1000.0
}

fn row(layout: &str, item: &str, t: Instant, note: &str) {
    println!("ROW|{layout}|{item}|{:.2}|{note}", ms(t));
}

/// 약 N글자. `line_len`글자마다 줄바꿈(0이면 한 줄). 한글·영문·숫자 혼합.
fn make_text(n: usize, line_len: usize) -> String {
    let unit: Vec<char> = "한글 문장과 English 123, 검색어 찾기 가나다라마바사.".chars().collect();
    let mut s = String::with_capacity(n * 3);
    for i in 0..n {
        if line_len > 0 && i % line_len == line_len - 1 {
            s.push('\n');
        } else {
            s.push(unit[i % unit.len()]);
        }
    }
    s
}

fn run(layout: &str, line_len: usize) {
    let text = make_text(N, line_len);
    assert_eq!(text.chars().count(), N);
    let cs = SearchOpts { case_sensitive: true, whole_word: false };

    // 1) 빈 문서에 N글자 한 번에 삽입 / 실행취소 / 다시실행
    let mut d = Document::new();
    let t = Instant::now();
    d.insert(0, &text).unwrap();
    row(layout, "N글자 한 번에 삽입", t, &format!("{}줄", d.line_count()));
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소", t, "");
    assert_eq!(d.len(), 0);
    let t = Instant::now();
    d.redo().unwrap();
    row(layout, "└ 다시실행", t, "");
    assert_eq!(d.text(), text);

    // 2) 전체 삭제 / 실행취소 / 다시실행
    d.commit();
    let t = Instant::now();
    let len = d.len();
    d.delete(0, len).unwrap();
    row(layout, "N글자 전체 삭제", t, "");
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소", t, "");
    let t = Instant::now();
    d.redo().unwrap();
    row(layout, "└ 다시실행", t, "");
    d.undo().unwrap();
    assert_eq!(d.text(), text);

    // 3) 가운데 10% 삭제 / 실행취소
    d.commit();
    let (a, b) = {
        let t = d.text();
        let a = t.char_indices().nth(N * 45 / 100).unwrap().0;
        let b = t.char_indices().nth(N * 55 / 100).unwrap().0;
        (a, b)
    };
    let t = Instant::now();
    d.delete(a, b).unwrap();
    row(layout, "가운데 10% 삭제", t, "");
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소", t, "");

    // 4) 한 글자씩 이어 입력 (같은 자리, 한 묶음) + 한 번에 실행취소
    d.commit();
    let typed = N / 10;
    let base = a;
    let t = Instant::now();
    for i in 0..typed {
        d.insert(base + i * 3, "글").unwrap();
    }
    let e = ms(t);
    println!("ROW|{layout}|이어 입력 {typed}자(글자당)|{:.2}|합계 {:.1} ms", e * 1000.0 / typed as f64, e);
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소 1회(묶음)", t, "");
    assert_eq!(d.text(), text);

    // 5) Backspace 연속 (끝에서 앞으로) + 한 번에 실행취소
    d.commit();
    let erase = N / 10;
    // 지울 글자의 시작 위치를 미리 계산(루프 안에서 text()를 부르면 갭 이동 비용이 섞인다)
    let starts: Vec<usize> = {
        let s = d.text();
        s[..b].char_indices().rev().take(erase).map(|(i, _)| i).collect()
    };
    let t = Instant::now();
    let mut pos = b;
    for &prev in &starts {
        d.delete(prev, pos).unwrap();
        pos = prev;
    }
    let e = ms(t);
    println!("ROW|{layout}|Backspace {erase}회(회당)|{:.2}|합계 {:.1} ms", e * 1000.0 / erase as f64, e);
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소 1회(묶음)", t, "");
    assert_eq!(d.text(), text);

    // 6) 무작위 위치 1글자 입력 2000회 (묶음 분리) → 지연
    let mut seed = 11u64;
    let t = Instant::now();
    for _ in 0..2000 {
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let line = (seed >> 33) as usize % d.line_count();
        let pos = d.line_start(line);
        d.commit();
        d.insert(pos, "가").unwrap();
    }
    let e = ms(t);
    println!("ROW|{layout}|무작위 위치 입력(회당)|{:.3}|2000회 합계 {:.1} ms", e / 2000.0, e);
    let t = Instant::now();
    for _ in 0..2000 {
        d.undo().unwrap();
    }
    row(layout, "└ 2000단계 실행취소", t, "");
    assert_eq!(d.text(), text);

    // 7) 줄·열 계산(문서 끝), 상태 값
    let t = Instant::now();
    let end = d.len();
    let (l, c) = d.line_col(end).unwrap();
    row(layout, "줄·열(문서 끝) 1회", t, &format!("{l}줄 {c}열"));

    // 8) 모두 바꾸기(한 번의 실행취소)
    d.commit();
    let t = Instant::now();
    let n = d.replace_all("검색어", "찾는말", cs).unwrap();
    row(layout, "모두 바꾸기", t, &format!("{n}건"));
    let t = Instant::now();
    d.undo().unwrap();
    row(layout, "└ 실행취소(1단위)", t, "");
    assert_eq!(d.text(), text);
}

#[test]
fn perf_million_chars() {
    println!("ROW|입력|{N}글자|0|");
    run("여러 줄(줄당 40자)", 40);
    run("한 줄", 0);
    run("짧은 줄(줄당 4자)", 4);
}

#[test]
fn perf_million_chars_encodings() {
    use editor_core::fileio::{self, Encoding};
    let text = make_text(N, 40);
    for enc in [Encoding::Utf8, Encoding::Utf16Le, Encoding::Cp949] {
        let t = Instant::now();
        let bytes = fileio::encode(&text, enc).unwrap();
        row(enc.name(), "N글자 저장용 변환", t, &format!("{} 바이트", bytes.len()));
        let t = Instant::now();
        let (back, found) = fileio::decode(&bytes).unwrap();
        row(enc.name(), "└ 열기(자동 감지)", t, &format!("감지 {}", found.name()));
        assert_eq!(back, text);
    }
    // 상태 값(줄·열·글자 수) 한 번: 한 줄 문서의 가운데 / 여러 줄 문서의 가운데
    let mut d = Document::from_text(&text);
    let pos = d.offset_of(d.line_count() / 2, 20);
    let t = Instant::now();
    let st = d.status(pos, Some((0, pos))).unwrap();
    row("상태", "상태 표시줄 값 1회(여러 줄 가운데)", t, &format!("{}줄 {}열 {}자 선택 {:?}", st.line, st.col, st.chars, st.selected_chars));
    let one = make_text(N, 0);
    let d = Document::from_text(&one);
    let pos = d.offset_of(1, N / 2);
    let t = Instant::now();
    let st = d.status(pos, None).unwrap();
    row("상태", "상태 표시줄 값 1회(한 줄 가운데)", t, &format!("{}줄 {}열", st.line, st.col));
    assert_eq!(st.col, N / 2);
}
