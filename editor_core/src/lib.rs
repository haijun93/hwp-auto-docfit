//! editor_core — 메모 편집기용 Rust 코어(std만 사용).
//!
//! * [`buffer::TextBuffer`] 갭 버퍼 + 줄 색인 (UTF-8 글자 경계 안전)
//! * [`doc::Document`] 실행취소/다시실행(입력 묶음), 찾기·바꾸기, 저장·자동 저장
//! * [`markdown`] 간단 Markdown 해석과 서식 적용/해제
//! * [`api::Engine`] JSON 한 줄 명령 → JSON 한 줄 응답 (klib 파이프 명령으로 노출하기 쉬운 형태)

pub mod api;
pub mod buffer;
pub mod doc;
pub mod fileio;
pub mod json;
pub mod markdown;
pub mod search;

pub use doc::Document;
