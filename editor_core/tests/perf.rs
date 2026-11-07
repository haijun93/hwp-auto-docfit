//! 큰 글(10만 줄) 성능 측정. `cargo test --release --test perf -- --nocapture`로 숫자를 본다.
//! 기준은 느슨하게(디버그 빌드에서도 통과) 두고, 실제 숫자는 출력해 docs에 기록한다.

use editor_core::api::Engine;
use editor_core::doc::Document;
use editor_core::markdown;
use editor_core::search::SearchOpts;
use std::time::Instant;

fn big_text(lines: usize) -> String {
    let mut s = String::with_capacity(lines * 64);
    for i in 0..lines {
        match i % 10 {
            0 => s.push_str(&format!("# 제목 {i}\n")),
            3 => s.push_str(&format!("- 목록 **굵게** 항목 {i} 가나다라마바사\n")),
            _ => s.push_str(&format!("{i}번째 줄: 한글 문장과 English text, 검색어 찾기 `code` 입니다.\n")),
        }
    }
    s
}

fn ms(t: Instant) -> f64 {
    t.elapsed().as_secs_f64() * 1000.0
}

#[test]
fn perf_100k_lines() {
    let text = big_text(100_000);
    let mb = text.len() as f64 / 1_048_576.0;
    println!("PERF 입력: 100000줄, {:.2} MB, {} 글자", mb, text.chars().count());
    let cs = SearchOpts { case_sensitive: true, whole_word: false };
    let ci = SearchOpts { case_sensitive: false, whole_word: false };

    let t = Instant::now();
    let mut d = Document::from_text(&text);
    println!("PERF 불러오기(LF 통일+색인): {:.1} ms", ms(t));
    assert_eq!(d.line_count(), 100_001);

    // 가운데·처음·끝 무작위 위치에 1글자씩 입력 4000회 (매번 묶음 분리)
    let t = Instant::now();
    let mut seed = 7u64;
    for _ in 0..4000 {
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let line = (seed >> 33) as usize % d.line_count();
        let pos = d.line_start(line);
        d.commit();
        d.insert(pos, "한").unwrap();
    }
    let e = ms(t);
    println!("PERF 무작위 위치 입력 4000회: {:.1} ms (회당 {:.1} µs)", e, e * 1000.0 / 4000.0);

    // 한 위치에서 이어 입력 20000자(실제 타이핑)
    let t = Instant::now();
    let base = d.line_start(50_000);
    for i in 0..20_000 {
        d.insert(base + i * 3, "글").unwrap();
    }
    let e = ms(t);
    println!("PERF 같은 위치 이어 입력 20000자: {:.1} ms (회당 {:.2} µs)", e, e * 1000.0 / 20000.0);

    let t = Instant::now();
    let (l, c) = d.line_col(d.len() / 2 - d.len() / 2 % 3).unwrap_or((0, 0));
    println!("PERF 줄·열 계산 1회: {:.3} ms ({l}줄 {c}열)", ms(t));

    let t = Instant::now();
    let st = d.stats();
    println!("PERF 통계(줄·글자·낱말): {:.1} ms → 줄 {} 글자 {} 낱말 {}", ms(t), st.lines, st.chars, st.words);

    let t = Instant::now();
    let n = d.find_all("검색어", cs, usize::MAX).len();
    println!("PERF 찾기(대소문자 구분) 모두: {:.1} ms → {n}건", ms(t));
    let t = Instant::now();
    let n = d.find_all("ENGLISH", ci, usize::MAX).len();
    println!("PERF 찾기(대소문자 무시) 모두: {:.1} ms → {n}건", ms(t));

    let t = Instant::now();
    let n = d.replace_all("검색어", "찾는말", cs).unwrap();
    println!("PERF 모두 바꾸기: {:.1} ms → {n}건", ms(t));
    let t = Instant::now();
    d.undo();
    println!("PERF 모두 바꾸기 실행취소: {:.1} ms", ms(t));

    let t = Instant::now();
    let blocks = markdown::parse(&d, 0, d.line_count());
    println!("PERF Markdown 전체 해석: {:.1} ms → {}블록", ms(t), blocks.len());
    let t = Instant::now();
    let v = markdown::parse(&d, 50_000, 50_060);
    println!("PERF Markdown 화면 구간(60줄) 해석: {:.1} ms → {}블록", ms(t), v.len());

    let dir = std::env::temp_dir().join(format!("editor_core_perf_{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let t = Instant::now();
    d.save(&dir.join("big.txt")).unwrap();
    println!("PERF 저장(임시 파일 후 교체): {:.1} ms", ms(t));
    let t = Instant::now();
    let d2 = Document::open(&dir.join("big.txt")).unwrap();
    println!("PERF 파일 열기: {:.1} ms → {}줄", ms(t), d2.line_count());
    let _ = std::fs::remove_dir_all(&dir);

    // 입력 4000회+이어 입력(1묶음) 전부 실행취소 (묶음 수만큼)
    let t = Instant::now();
    let mut steps = 0;
    while d.undo().is_some() {
        steps += 1;
    }
    println!("PERF 전체 실행취소: {:.1} ms → {steps}단계", ms(t));
    assert_eq!(d.text(), text);

    // JSON 왕복(API 경유) 1000회 입력
    let mut eng = Engine::new();
    let r = eng.handle(r#"{"cmd":"edit_open","text":""}"#);
    assert!(r.contains("\"doc\":1"));
    let t = Instant::now();
    for i in 0..1000 {
        let r = eng.handle(&format!(r#"{{"cmd":"edit_insert","doc":1,"pos":{},"text":"가"}}"#, i * 3));
        assert!(r.starts_with("{\"ok\":true"));
    }
    let e = ms(t);
    println!("PERF JSON 명령 1000회: {:.1} ms (회당 {:.1} µs)", e, e);
}
