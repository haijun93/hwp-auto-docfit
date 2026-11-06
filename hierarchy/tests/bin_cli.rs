use std::io::Write;
use std::process::{Command, Stdio};

fn run(input: &str) -> (bool, String) {
    let mut c = Command::new(env!("CARGO_BIN_EXE_hierarchy")).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn().unwrap();
    c.stdin.take().unwrap().write_all(input.as_bytes()).unwrap();
    let o = c.wait_with_output().unwrap();
    (o.status.success(), String::from_utf8(o.stdout).unwrap())
}

#[test]
fn analyzes_paragraphs() {
    let (ok, out) = run(r#"{"paragraphs":[{"text":"1. 추진 배경","indent":0,"font_size":15},{"text":"가. 세부","indent":10,"font_size":13},{"text":"일반 문장😀","indent":0,"font_size":12}]}"#);
    assert!(ok);
    assert!(out.starts_with("{\"levels\":["), "{}", out);
    assert!(out.contains("\"confidence\":") && out.contains("\"ambiguous\":[") && out.contains("\"diagnostics\":["));
}
#[test]
fn empty_and_invalid() {
    let (ok, out) = run(r#"{"paragraphs":[]}"#);
    assert!(ok && out.contains("\"levels\":[]"));
    assert!(!run("not json").0);
}
