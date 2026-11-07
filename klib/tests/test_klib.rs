//! 가상 관계형 자료함 엔진 통합 테스트.
//! CRUD, 자료 추가/사본, 공간 이동, 관계선, 검색, 물리 폴더 전환, IPC 통신, 격리 검증.

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::AtomicBool;
use std::sync::{Arc, Mutex, MutexGuard};

// klib 내부 모듈 접근을 위한 선언 (크레이트 바이너리 테스트)
#[path = "../src/scan.rs"]
mod scan;
#[path = "../src/db.rs"]
mod db;
#[path = "../src/json.rs"]
mod json;
#[path = "../src/pipe.rs"]
mod pipe;
#[path = "../src/util.rs"]
mod util;
#[path = "../src/search.rs"]
mod search;
#[path = "../src/notebook.rs"]
mod notebook;
#[path = "../src/nb_transform.rs"]
mod nb_transform;
#[path = "../src/content.rs"]
mod content;

static SEARCH_INDEX: std::sync::OnceLock<Result<search::SearchIndex, String>> = std::sync::OnceLock::new();
fn search_index() -> Result<&'static search::SearchIndex, String> {
    // 시험마다 지우는 KLIB_TEST_ROOT가 아니라 프로세스 단위 폴더에 둔다(먼저 부른 시험의 폴더에 묶이면 순서에 따라 실패).
    SEARCH_INDEX.get_or_init(|| { let dir=std::env::var("KLIB_TANTIVY_DIR").unwrap_or_else(|_| std::env::temp_dir().join(format!("klib-test-tantivy-{}", std::process::id())).to_string_lossy().into_owned()); search::SearchIndex::open_or_create(dir).map_err(|e|e.to_string()) }).as_ref().map_err(Clone::clone)
}

use db::Database;
use json::Value;

static TEST_MUTEX: Mutex<()> = Mutex::new(());

struct TestContext {
    dir: PathBuf,
    _guard: MutexGuard<'static, ()>,
}

impl TestContext {
    fn new(name: &str) -> Self {
        let guard = TEST_MUTEX.lock().unwrap();
        let dir = std::env::temp_dir().join(format!("klib-test-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        unsafe {
            std::env::set_var("KLIB_TEST_ROOT", dir.to_str().unwrap());
        }
        TestContext { dir, _guard: guard }
    }
}

impl Drop for TestContext {
    fn drop(&mut self) {
        unsafe {
            std::env::remove_var("KLIB_TEST_ROOT");
        }
        let _ = fs::remove_dir_all(&self.dir);
    }
}

#[test]
fn test_box_crud() {
    let ctx = TestContext::new("box_crud");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();

    // Create
    let b1 = db.box_create("프로젝트A", "보고서 준비용 자료함").unwrap();
    assert!(b1 > 0);

    // List
    let list = db.box_list().unwrap();
    assert_eq!(list.len(), 1);
    assert_eq!(list[0].name, "프로젝트A");
    assert_eq!(list[0].description, "보고서 준비용 자료함");
    assert_eq!(list[0].item_count, 0);

    // Get
    let detail = db.box_get(b1).unwrap().expect("자료함 존재");
    assert_eq!(detail.0.name, "프로젝트A");
    assert!(detail.1.is_empty());
    assert!(detail.2.is_empty());

    // Update
    let updated = db.box_update(b1, "프로젝트A-수정", "설명 변경").unwrap();
    assert!(updated);
    let detail2 = db.box_get(b1).unwrap().unwrap();
    assert_eq!(detail2.0.name, "프로젝트A-수정");
    assert_eq!(detail2.0.description, "설명 변경");

    // Delete
    let deleted = db.box_delete(b1).unwrap();
    assert!(deleted);
    assert!(db.box_get(b1).unwrap().is_none());
}

#[test]
fn test_item_types_and_copy() {
    let ctx = TestContext::new("item_types");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("자료형식시험", "").unwrap();

    // 1. 파일
    let sample_file = ctx.dir.join("sample.hwp");
    fs::write(&sample_file, "한글문서내용").unwrap();
    let it_file = db.item_add(b1, "file", sample_file.to_str().unwrap(), "표준서식.hwp", "basis", 10.0, 20.0, None).unwrap();
    assert!(it_file > 0);

    // 2. 글 (데이터 폴더에 사본 보관)
    let it_text = db.item_add(b1, "text", "", "회의메모", "core", 50.0, 60.0, Some("2026-11-03 회의 안건 내용")).unwrap();
    let text_row = db.item_get(it_text).unwrap().unwrap();
    assert!(Path::new(&text_row.source_path).is_file());
    let saved_text = fs::read_to_string(&text_row.source_path).unwrap();
    assert_eq!(saved_text, "2026-11-03 회의 안건 내용");

    // 3. 그림 (Base64 사본 보관)
    let png_header_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
    let it_img = db.item_add(b1, "image", "", "스크린샷1", "temp", 0.0, 0.0, Some(png_header_b64)).unwrap();
    let img_row = db.item_get(it_img).unwrap().unwrap();
    assert!(Path::new(&img_row.source_path).is_file());
    assert!(img_row.source_path.ends_with(".png"));

    // 4. 링크
    let it_link = db.item_add(b1, "link", "https://example.com/doc", "참고링크", "reference", 30.0, 40.0, None).unwrap();
    let link_row = db.item_get(it_link).unwrap().unwrap();
    assert_eq!(link_row.source_path, "https://example.com/doc");

    // 개수 확인
    let list = db.box_list().unwrap();
    assert_eq!(list[0].item_count, 4);
}

#[test]
fn test_item_move_and_coordinates() {
    let ctx = TestContext::new("item_move");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("이동시험", "").unwrap();

    let it = db.item_add(b1, "note", "", "메모1", "temp", 0.0, 0.0, Some("내용")).unwrap();
    let it_row = db.item_get(it).unwrap().unwrap();
    assert_eq!(it_row.space, "temp");
    assert_eq!(it_row.x, 0.0);
    assert_eq!(it_row.y, 0.0);

    // 공간 이동: temp -> core, 좌표: (150.5, 300.0)
    let moved = db.item_move(it, "core", 150.5, 300.0).unwrap();
    assert!(moved);

    let moved_row = db.item_get(it).unwrap().unwrap();
    assert_eq!(moved_row.space, "core");
    assert_eq!(moved_row.x, 150.5);
    assert_eq!(moved_row.y, 300.0);

    // 유효하지 않은 공간명 거부 검증
    let invalid = db.item_move(it, "invalid_space", 10.0, 10.0);
    assert!(invalid.is_err());
}

#[test]
fn test_relation_crud() {
    let ctx = TestContext::new("relation_crud");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("관계시험", "").unwrap();
    let it1 = db.item_add(b1, "text", "", "핵심기록", "core", 10.0, 10.0, Some("핵심")).unwrap();
    let it2 = db.item_add(b1, "note", "", "근거메모", "core", 100.0, 10.0, Some("근거")).unwrap();

    // 관계선 추가
    let rel_id = db.relation_add(b1, it1, it2, "근거 자료 연결").unwrap();
    assert!(rel_id > 0);

    // 자기 자신에 대한 관계선 거부 확인
    let self_rel = db.relation_add(b1, it1, it1, "자기 연결");
    assert!(self_rel.is_err());

    // 관계선 목록
    let list = db.relation_list(b1).unwrap();
    assert_eq!(list.len(), 1);
    assert_eq!(list[0].from_item, it1);
    assert_eq!(list[0].to_item, it2);
    assert_eq!(list[0].label, "근거 자료 연결");

    // 다른 자료함의 항목과 연결 시도 시 거부 확인
    let b2 = db.box_create("다른자료함", "").unwrap();
    let it3 = db.item_add(b2, "note", "", "타자료", "temp", 0.0, 0.0, Some("타")).unwrap();
    let cross_err = db.relation_add(b1, it1, it3, "교차 연결 시도");
    assert!(cross_err.is_err());

    // 존재하지 않는 자료함 ID 또는 항목 ID로 관계선 시도 시 거부 확인 (지적 2)
    let non_exist_box = db.relation_add(99999, it1, it2, "없는 자료함");
    assert!(non_exist_box.is_err());
    let non_exist_err = db.relation_add(b1, 9999, 9998, "없는 연결");
    assert!(non_exist_err.is_err());

    // 관계선 삭제
    let del = db.relation_delete(rel_id).unwrap();
    assert!(del);
    assert!(db.relation_list(b1).unwrap().is_empty());
}

#[test]
fn test_item_search() {
    let ctx = TestContext::new("item_search");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("자료함1", "").unwrap();
    let b2 = db.box_create("자료함2", "").unwrap();

    db.item_add(b1, "text", "", "2026년 업무보고서.hwpx", "core", 0.0, 0.0, Some("내용")).unwrap();
    db.item_add(b1, "text", "", "예산 집행 계획.txt", "basis", 0.0, 0.0, Some("내용")).unwrap();
    db.item_add(b2, "text", "", "기타 보고서.hwpx", "temp", 0.0, 0.0, Some("내용")).unwrap();

    // 1. 특정 자료함 검색
    let res1 = db.item_search(Some(b1), "보고서").unwrap();
    assert_eq!(res1.len(), 1);
    assert_eq!(res1[0].display_name, "2026년 업무보고서.hwpx");

    // 2. 전체 자료함 검색
    let res2 = db.item_search(None, "보고서").unwrap();
    assert_eq!(res2.len(), 2);

    // 3. 대소문자 무시 검색
    let res3 = db.item_search(Some(b1), "HWPX").unwrap();
    assert_eq!(res3.len(), 1);
}

#[test]
fn test_physical_folder_export() {
    let ctx = TestContext::new("export");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("물리전환시험", "").unwrap();

    // 원본 파일 준비
    let original_file = ctx.dir.join("원본문서.txt");
    fs::write(&original_file, "원본 불변 데이터").unwrap();

    // core 공간에 파일 추가
    db.item_add(b1, "file", original_file.to_str().unwrap(), "원본문서.txt", "core", 0.0, 0.0, None).unwrap();
    // core 공간에 중복 이름 파일 하나 더 추가 (충돌 회피 검사)
    db.item_add(b1, "file", original_file.to_str().unwrap(), "원본문서.txt", "core", 10.0, 10.0, None).unwrap();
    // basis 공간에 글 추가
    db.item_add(b1, "text", "", "기초메모", "basis", 0.0, 0.0, Some("기초 지식 정리")).unwrap();
    // reference 공간에 링크 추가
    db.item_add(b1, "link", "https://gov.kr", "전자정부", "reference", 0.0, 0.0, None).unwrap();

    // 물리 폴더로 전환
    let export_dir = ctx.dir.join("내보내기폴더");
    let count = db.box_export(b1, export_dir.to_str().unwrap()).unwrap();
    assert_eq!(count, 4);

    // 원본 파일 보존 확인
    assert_eq!(fs::read_to_string(&original_file).unwrap(), "원본 불변 데이터");

    // 공간별 하위 폴더 존재 확인
    assert!(export_dir.join("1_핵심자료").is_dir());
    assert!(export_dir.join("2_기초자료").is_dir());
    assert!(export_dir.join("3_참고자료").is_dir());
    assert!(export_dir.join("4_임시저장소").is_dir());

    // 1_핵심자료에 충돌 회피 파일 확인 (원본문서.txt 및 원본문서 (1).txt)
    assert!(export_dir.join("1_핵심자료").join("원본문서.txt").is_file());
    assert!(export_dir.join("1_핵심자료").join("원본문서 (1).txt").is_file());

    // 2_기초자료에 텍스트 파일 생성 확인
    assert!(export_dir.join("2_기초자료").join("기초메모.txt").is_file());
    assert_eq!(fs::read_to_string(export_dir.join("2_기초자료").join("기초메모.txt")).unwrap(), "기초 지식 정리");

    // 3_참고자료에 URL 바로가기 파일 생성 확인
    let url_file = export_dir.join("3_참고자료").join("전자정부.url");
    assert!(url_file.is_file());
    let url_content = fs::read_to_string(url_file).unwrap();
    assert!(url_content.contains("URL=https://gov.kr"));

    // DB에 export_path 기록 확인
    let box_info = db.box_get(b1).unwrap().unwrap().0;
    assert_eq!(box_info.export_path, Some(export_dir.to_str().unwrap().to_string()));
}

#[cfg(windows)]
#[test]
fn test_physical_folder_export_reparse_point_rolls_back() {
    use std::os::windows::fs::symlink_file;

    let ctx = TestContext::new("export_reparse");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("링크 포함 폴더 전환", "").unwrap();

    let source_dir = ctx.dir.join("원본폴더");
    fs::create_dir_all(&source_dir).unwrap();
    let source_file = source_dir.join("정상파일.txt");
    fs::write(&source_file, "원본 내용").unwrap();
    let link_target = ctx.dir.join("링크대상.txt");
    fs::write(&link_target, "링크 대상").unwrap();
    symlink_file(&link_target, source_dir.join("하위링크.txt")).unwrap();

    db.item_add(b1, "folder", source_dir.to_str().unwrap(), "원본폴더", "core", 0.0, 0.0, None).unwrap();

    let export_dir = ctx.dir.join("불완전전환");
    let error = db.box_export(b1, export_dir.to_str().unwrap()).unwrap_err();
    assert!(error.contains("폴더 복사 실패"));
    assert!(error.contains("심볼릭 링크나 정션"));
    assert!(!export_dir.exists(), "실패한 내보내기 산출물은 롤백되어야 합니다");

    let box_info = db.box_get(b1).unwrap().unwrap().0;
    assert_eq!(box_info.export_path, None, "실패한 전환 경로를 DB에 기록하면 안 됩니다");
    assert_eq!(fs::read_to_string(source_file).unwrap(), "원본 내용");
    assert_eq!(fs::read_to_string(link_target).unwrap(), "링크 대상");
}

#[test]
fn test_pipe_ipc_communication() {
    let ctx = TestContext::new("pipe_ipc");
    let db = Arc::new(Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap()));
    let running = Arc::new(AtomicBool::new(true));

    // 1. ping
    let resp1 = pipe::handle_request(r#"{"cmd":"ping"}"#, &db, &running);
    let val1 = json::parse(&resp1).unwrap();
    assert_eq!(val1.bool("ok"), Some(true));
    assert_eq!(val1.str("message"), Some("pong"));

    // 2. box_create
    let resp2 = pipe::handle_request(r#"{"cmd":"box_create","name":"파이프자료함","description":"설명"}"#, &db, &running);
    let val2 = json::parse(&resp2).unwrap();
    assert_eq!(val2.bool("ok"), Some(true));
    let bid = val2.i64("id").unwrap();

    // 3. item_add
    let resp3 = pipe::handle_request(
        &format!(r#"{{"cmd":"item_add","box_id":{bid},"kind":"text","display_name":"기록","space":"temp","content":"내용"}}"#),
        &db,
        &running,
    );
    let val3 = json::parse(&resp3).unwrap();
    assert_eq!(val3.bool("ok"), Some(true));
    let iid = val3.i64("id").unwrap();

    // 4. item_move
    let resp4 = pipe::handle_request(
        &format!(r#"{{"cmd":"item_move","id":{iid},"space":"core","x":100.0,"y":200.0}}"#),
        &db,
        &running,
    );
    let val4 = json::parse(&resp4).unwrap();
    assert_eq!(val4.bool("ok"), Some(true));

    // 5. item_search
    let resp5 = pipe::handle_request(
        &format!(r#"{{"cmd":"item_search","box_id":{bid},"query":"기록"}}"#),
        &db,
        &running,
    );
    let val5 = json::parse(&resp5).unwrap();
    assert_eq!(val5.bool("ok"), Some(true));
    let items = val5.arr("items").unwrap();
    assert_eq!(items.len(), 1);

    // 6. quit
    let resp6 = pipe::handle_request(r#"{"cmd":"quit"}"#, &db, &running);
    let val6 = json::parse(&resp6).unwrap();
    assert_eq!(val6.bool("ok"), Some(true));
    assert!(!running.load(std::sync::atomic::Ordering::Relaxed));
}

#[test]
fn test_reparse_point_rejection() {
    let ctx = TestContext::new("reparse");
    let regular_file = ctx.dir.join("normal.txt");
    fs::write(&regular_file, "normal").unwrap();
    assert!(!util::is_reparse_point(&regular_file));
    assert!(!util::is_or_has_reparse_point(&regular_file));
}

#[test]
fn test_json_strictness_and_surrogates() {
    assert!(json::parse("+1").is_none());
    assert!(json::parse("01").is_none());
    assert!(json::parse("1.").is_none());
    assert!(json::parse("1e").is_none());
    assert!(json::parse("x").is_none());
    assert_eq!(json::parse("0").unwrap().num("").unwrap_or(0.0), 0.0);
    assert!(matches!(json::parse("-12.34").unwrap(), json::Value::Num(n) if n == -12.34));

    assert!(json::parse(r#""abc"#).is_none());
    assert!(json::parse("\"\x01\"").is_none());

    let parsed_emoji = json::parse(r#""\uD83D\uDE00""#).unwrap();
    match parsed_emoji {
        Value::Str(s) => assert_eq!(s, "😀"),
        _ => panic!("문자열이어야 함"),
    }

    assert!(json::parse(r#""\uD83D""#).is_none());
    assert!(json::parse(r#""\uDE00""#).is_none());
}

#[test]
fn test_item_add_nonexistent_box_rejection() {
    let ctx = TestContext::new("nonexistent_box");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let res = db.item_add(99999, "text", "", "메모", "core", 0.0, 0.0, Some("내용"));
    assert!(res.is_err());
}

#[test]
fn test_path_traversal_prevention() {
    let ctx = TestContext::new("path_traversal");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("경로탈출방지", "").unwrap();

    // display_name에 상위 경로 탈출(../ 또는 ..\..) 주입
    let evil_name = "../../escape_attempt.txt";
    db.item_add(b1, "text", "", evil_name, "core", 0.0, 0.0, Some("탈출 시도")).unwrap();

    let export_dir = ctx.dir.join("export_safe");
    let count = db.box_export(b1, export_dir.to_str().unwrap()).unwrap();
    assert_eq!(count, 1);

    // export_dir 바로 아래나 상위 경로에 생성되지 않고, 반드시 1_핵심자료 안에 안전하게 정규화되어 생성되어야 함
    assert!(!export_dir.join("escape_attempt.txt").exists());
    assert!(!ctx.dir.join("escape_attempt.txt").exists());
    let core_files: Vec<_> = fs::read_dir(export_dir.join("1_핵심자료")).unwrap().map(|e| e.unwrap().file_name().to_string_lossy().to_string()).collect();
    assert_eq!(core_files.len(), 1);
    assert!(!core_files[0].contains('/'));
    assert!(!core_files[0].contains('\\'));
    assert!(core_files[0].ends_with(".txt"));
}

#[test]
fn test_export_non_empty_rejection_and_rollback() {
    let ctx = TestContext::new("export_rollback");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("전환검증자료함", "").unwrap();

    let sample = ctx.dir.join("valid.txt");
    fs::write(&sample, "정상내용").unwrap();
    db.item_add(b1, "file", sample.to_str().unwrap(), "valid.txt", "core", 0.0, 0.0, None).unwrap();

    // 1. 이미 파일이 들어있는 비어있지 않은 폴더로 내보내기 시도 -> 거부 확인
    let non_empty_dir = ctx.dir.join("existing_folder");
    fs::create_dir_all(&non_empty_dir).unwrap();
    fs::write(non_empty_dir.join("existing.txt"), "기존데이터").unwrap();

    let err = db.box_export(b1, non_empty_dir.to_str().unwrap());
    assert!(err.is_err());
    assert_eq!(fs::read_to_string(non_empty_dir.join("existing.txt")).unwrap(), "기존데이터");
    assert!(!non_empty_dir.join("1_핵심자료").exists());

    // 2. 존재하지 않던 신규 폴더로 내보내기 시 원자적 롤백 시험
    // 유효하지 않은 원본 경로를 가진 아이템을 강제로 DB에 넣어 내보내기 실패 유발
    let bad_b = db.box_create("오류자료함", "").unwrap();
    let phantom_file = ctx.dir.join("phantom.txt");
    // 파일 생성 후 등록, 그 뒤 파일 삭제하여 내보내기 시 원본 누락 에러 유발
    fs::write(&phantom_file, "삭제예정").unwrap();
    db.item_add(bad_b, "file", phantom_file.to_str().unwrap(), "phantom.txt", "core", 0.0, 0.0, None).unwrap();
    let _ = fs::remove_file(&phantom_file);

    let target_fail = ctx.dir.join("fail_export_dir");
    let fail_res = db.box_export(bad_b, target_fail.to_str().unwrap());
    assert!(fail_res.is_err());
    // 실패 시 롤백되어 target_fail 폴더 자체가 남아있지 않아야 함
    assert!(!target_fail.exists());
}

#[test]
fn test_export_folder_reparse_point_rejection_and_rollback() {
    let ctx = TestContext::new("export_reparse");
    let db = Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap();
    let b1 = db.box_create("폴더정션검증", "").unwrap();

    let src_dir = ctx.dir.join("parent_folder");
    fs::create_dir_all(&src_dir).unwrap();
    fs::write(src_dir.join("normal.txt"), "일반자료").unwrap();

    let target_file = ctx.dir.join("target.txt");
    fs::write(&target_file, "대상내용").unwrap();
    let link_child = src_dir.join("link_child.txt");

    #[cfg(windows)]
    let link_created = std::os::windows::fs::symlink_file(&target_file, &link_child).is_ok();
    #[cfg(not(windows))]
    let link_created = std::os::unix::fs::symlink(&target_file, &link_child).is_ok();

    if link_created {
        assert!(util::is_or_has_reparse_point(&link_child));
        db.item_add(b1, "folder", src_dir.to_str().unwrap(), "parent_folder", "core", 0.0, 0.0, None).unwrap();

        let export_dir = ctx.dir.join("export_reparse_output");
        let res = db.box_export(b1, export_dir.to_str().unwrap());
        // 하위에 reparse point가 하나라도 있으면 전환 실패 및 롤백 확인
        assert!(res.is_err());
        assert!(!export_dir.exists());
    }
}

#[test]
fn test_copy_dir_recursive_reparse_point_rejection() {
    let ctx = TestContext::new("copy_dir_reparse");
    let src_dir = ctx.dir.join("src");
    fs::create_dir_all(&src_dir).unwrap();
    let target = ctx.dir.join("target.txt");
    fs::write(&target, "target").unwrap();
    let symlink = src_dir.join("link.txt");

    #[cfg(windows)]
    let link_created = std::os::windows::fs::symlink_file(&target, &symlink).is_ok();
    #[cfg(not(windows))]
    let link_created = std::os::unix::fs::symlink(&target, &symlink).is_ok();

    if link_created {
        let dest = ctx.dir.join("dst");
        let res = db::copy_dir_recursive(&src_dir, &dest);
        assert!(res.is_err());
        assert_eq!(res.unwrap_err().kind(), std::io::ErrorKind::InvalidData);
    }
}

#[test]
fn test_nb_source_add_structured_and_python_paragraphs() {
    let ctx = TestContext::new("nb_source_add");
    let db = Arc::new(Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap()));
    let running = Arc::new(AtomicBool::new(true));
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let nb = call(r#"{"cmd":"nb_create","name":"노트"}"#.into()).i64("id").unwrap();

    // klib 직접 추출: md 제목 수준과 기호 수준이 문단에 남는다.
    let md = ctx.dir.join("계획.md");
    fs::write(&md, "# 추진 계획\n□ 예산 현황\n본문\n").unwrap();
    let md_path = md.to_str().unwrap().replace(std::path::MAIN_SEPARATOR, "/");
    let added = call(format!(r#"{{"cmd":"nb_source_add","notebook_id":{nb},"source_path":"{md_path}"}}"#));
    assert_eq!(added.bool("ok"), Some(true), "{added:?}");
    assert_eq!(added.i64("paragraph_count"), Some(3));
    let outline = call(format!(r#"{{"cmd":"nb_transform","notebook_id":{nb},"type":"outline"}}"#));
    let rows = outline.arr("results").unwrap();
    assert_eq!(rows.iter().map(|r| (r.str("text").unwrap(), r.i64("level").unwrap())).collect::<Vec<_>>(), vec![("추진 계획", 1), ("□ 예산 현황", 3)]);

    // 구형 hwp·pdf는 klib가 직접 읽지 않는다.
    let pdf = ctx.dir.join("자료.pdf");
    fs::write(&pdf, b"%PDF-1.4").unwrap();
    let pdf_path = pdf.to_str().unwrap().replace(std::path::MAIN_SEPARATOR, "/");
    let refused = call(format!(r#"{{"cmd":"nb_source_add","notebook_id":{nb},"source_path":"{pdf_path}"}}"#));
    assert_eq!(refused.bool("ok"), Some(false));

    // Python 추출 문단을 첫 묶음으로 받고, 나머지 묶음은 nb_index로 덧붙인다.
    let first = call(format!(r#"{{"cmd":"nb_source_add","notebook_id":{nb},"source_path":"{pdf_path}","paragraphs":[{{"text":"Ⅰ. 개요","level":1,"location":"1쪽"}},{{"text":"구분\t금액","table":true}}]}}"#));
    assert_eq!(first.bool("ok"), Some(true), "{first:?}");
    let sid = first.i64("id").unwrap();
    let more = call(format!(r#"{{"cmd":"nb_index","notebook_id":{nb},"source_id":{sid},"paragraphs":[{{"text":"예산\t1,250만원","kind":"table"}}]}}"#));
    assert_eq!(more.i64("paragraph_count"), Some(3), "{more:?}");
    let ps = call(format!(r#"{{"cmd":"nb_source_paragraphs","notebook_id":{nb},"source_id":{sid}}}"#));
    let ps = ps.arr("paragraphs").unwrap();
    assert_eq!(ps.iter().map(|p| p.i64("ordinal").unwrap()).collect::<Vec<_>>(), vec![0, 1, 2]);
    assert_eq!(ps[0].str("location"), Some("1쪽"));
    let tables = call(format!(r#"{{"cmd":"nb_transform","notebook_id":{nb},"type":"tables","source_ids":[{sid}]}}"#));
    assert_eq!(tables.arr("results").unwrap().iter().map(|r| r.str("text").unwrap()).collect::<Vec<_>>(), vec!["구분\t금액", "예산\t1,250만원"]);
    let hits = call(format!(r#"{{"cmd":"nb_search","notebook_id":{nb},"query":"1,250만원","source_ids":[{sid}]}}"#));
    assert!(!hits.arr("results").unwrap().is_empty(), "{hits:?}");
}

#[test]
fn test_nb_note_tags_compare_and_export() {
    let ctx = TestContext::new("nb_tags_compare");
    let db = Arc::new(Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap()));
    let running = Arc::new(AtomicBool::new(true));
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let nb = call(r#"{"cmd":"nb_create","name":"비교"}"#.into()).i64("id").unwrap();
    let add = |name: &str, text: &str| {
        let path = ctx.dir.join(name);
        fs::write(&path, text).unwrap();
        let path = path.to_str().unwrap().replace(std::path::MAIN_SEPARATOR, "/");
        let added = call(format!(r#"{{"cmd":"nb_source_add","notebook_id":{nb},"source_path":"{path}"}}"#));
        assert_eq!(added.bool("ok"), Some(true), "{added:?}");
        added.i64("id").unwrap()
    };
    let a = add("가.txt", "복지 예산은 120억 원이다\n도로 정비\n복지 예산 복지 예산 증가\n");
    let b = add("나.txt", "복지 지원 확대\n");
    let c = add("다.txt", "무관한 내용\n");

    // 출처별 비교: 출처마다 따로 찾고, 근거가 없는 출처도 빈 칸으로 낸다.
    let cmp = call(format!(r#"{{"cmd":"nb_compare","notebook_id":{nb},"query":"복지 예산","per_source":2}}"#));
    assert_eq!(cmp.bool("ok"), Some(true), "{cmp:?}");
    let groups = cmp.arr("groups").unwrap();
    assert_eq!(groups.iter().map(|g| g.i64("source_id").unwrap()).collect::<Vec<_>>(), vec![a, b, c]);
    assert_eq!(groups[0].arr("hits").unwrap().len(), 2);
    assert!(groups[0].arr("hits").unwrap().iter().all(|h| h.i64("source_id") == Some(a)));
    assert_eq!(groups[1].arr("hits").unwrap()[0].i64("ordinal"), Some(0));
    assert!(groups[2].arr("hits").unwrap().is_empty());
    let scoped = call(format!(r#"{{"cmd":"nb_compare","notebook_id":{nb},"query":"복지","source_ids":[{b}]}}"#));
    assert_eq!(scoped.arr("groups").unwrap().len(), 1);
    assert_eq!(call(format!(r#"{{"cmd":"nb_compare","notebook_id":{nb},"query":"  "}}"#)).bool("ok"), Some(false));
    assert_eq!(call(format!(r#"{{"cmd":"nb_compare","notebook_id":{nb},"query":"복지","source_ids":["x"]}}"#)).bool("ok"), Some(false));

    // 태그 저장·거르기·태그 목록.
    let saved = call(format!(r##"{{"cmd":"nb_note_save","notebook_id":{nb},"title":"메모","body":"본문","tags":["#예산"," 복지 정책 ","예산"],"citations":[{{"source_id":{a},"paragraph_ordinal":0,"quote":"복지 예산은 120억 원이다"}}]}}"##));
    assert_eq!(saved.bool("ok"), Some(true), "{saved:?}");
    let note = saved.i64("id").unwrap();
    assert!(matches!(saved.arr("tags").unwrap(), [Value::Str(x), Value::Str(y)] if x == "예산" && y == "복지_정책"), "{saved:?}");
    call(format!(r#"{{"cmd":"nb_note_save","notebook_id":{nb},"title":"다른","body":"","tags":["도로"]}}"#));
    let all = call(format!(r#"{{"cmd":"nb_note_list","notebook_id":{nb}}}"#));
    assert_eq!(all.arr("notes").unwrap().len(), 2);
    assert_eq!(all.arr("tags").unwrap().iter().map(|t| t.str("tag").unwrap()).collect::<Vec<_>>(), vec!["도로", "복지_정책", "예산"]);
    let filtered = call(format!(r#"{{"cmd":"nb_note_list","notebook_id":{nb},"tag":"예산"}}"#));
    let notes = filtered.arr("notes").unwrap();
    assert_eq!(notes.len(), 1);
    assert_eq!(notes[0].i64("id"), Some(note));
    assert_eq!(notes[0].arr("tags").unwrap().len(), 2);
    assert_eq!(notes[0].arr("citations").unwrap().len(), 1);
    // tags 없이 저장하면 태그를 그대로 둔다.
    call(format!(r#"{{"cmd":"nb_note_save","notebook_id":{nb},"id":{note},"title":"메모","body":"고친 본문","citations":[]}}"#));
    assert_eq!(call(format!(r#"{{"cmd":"nb_note_list","notebook_id":{nb},"tag":"복지_정책"}}"#)).arr("notes").unwrap().len(), 1);
    assert_eq!(call(format!(r#"{{"cmd":"nb_note_save","notebook_id":{nb},"title":"x","tags":[1]}}"#)).bool("ok"), Some(false));

    // 내보내기: 태그 줄과 출처 비교 절.
    let plain = call(format!(r#"{{"cmd":"nb_export_md","notebook_id":{nb},"note_id":{note}}}"#));
    let plain = plain.str("markdown").unwrap();
    assert!(plain.starts_with("# 메모\n\n태그: #예산 #복지_정책\n\n고친 본문"), "{plain}");
    assert!(!plain.contains("출처 비교"));
    let md = call(format!(r#"{{"cmd":"nb_export_md","notebook_id":{nb},"note_id":{note},"compare_query":"복지 예산","compare_source_ids":[{a},{c}],"per_source":1}}"#));
    let md = md.str("markdown").unwrap();
    assert!(md.contains("## 출처 비교: 복지 예산"), "{md}");
    assert!(md.contains("### 가.txt"));
    assert!(!md.contains("### 나.txt"));
    assert!(md.contains("### 다.txt"));
    assert!(md.contains("근거 문단 없음"));
}

#[test]
fn test_box_scan_pipe_commands_incremental_progress_cancel() {
    let ctx = TestContext::new("box_scan");
    let db = Arc::new(Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap()));
    let running = Arc::new(AtomicBool::new(true));
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let wait_done = || {
        for _ in 0..400 {
            let s = call(r#"{"cmd":"box_scan_status"}"#.into());
            if s.str("state") != Some("scanning") { return s; }
            std::thread::sleep(std::time::Duration::from_millis(25));
        }
        panic!("스캔이 끝나지 않음");
    };
    let b = call(r#"{"cmd":"box_create","name":"스캔"}"#.into()).i64("id").unwrap();

    assert_eq!(call(r#"{"cmd":"box_scan_status"}"#.into()).str("state"), Some("idle"));
    assert_eq!(call(r#"{"cmd":"box_scan_cancel"}"#.into()).bool("cancelling"), Some(false));

    let src = ctx.dir.join("폴더");
    fs::create_dir_all(src.join("하위")).unwrap();
    for i in 0..4 { fs::write(src.join(format!("f{i}.txt")), "x").unwrap(); }
    fs::write(src.join("하위").join("g.txt"), "y").unwrap();
    // 상위 폴더에 링크가 있으면(macOS /var) 스캔을 거부하므로 실제 경로로 바꾼다. Windows는 \\?\ 접두가 붙어 그대로 둔다.
    let src = if cfg!(windows) { src } else { fs::canonicalize(&src).unwrap() };
    let p = src.to_str().unwrap().replace('\\', "/");

    assert_eq!(call(format!(r#"{{"cmd":"box_scan","box_id":999,"path":"{p}"}}"#)).bool("ok"), Some(false));
    assert_eq!(call(format!(r#"{{"cmd":"box_scan","box_id":{b},"path":"{p}/없는폴더"}}"#)).bool("ok"), Some(false));

    let started = call(format!(r#"{{"cmd":"box_scan","box_id":{b},"path":"{p}"}}"#));
    assert_eq!(started.bool("started"), Some(true), "{:?}", started.str("message"));
    let s = wait_done();
    assert_eq!(s.str("state"), Some("done"));
    assert_eq!((s.i64("total"), s.i64("processed"), s.i64("added"), s.i64("unchanged")), (Some(5), Some(5), Some(5), Some(0)));

    call(format!(r#"{{"cmd":"box_scan","box_id":{b},"path":"{p}"}}"#));
    let s = wait_done();
    assert_eq!((s.i64("added"), s.i64("updated"), s.i64("unchanged"), s.i64("removed")), (Some(0), Some(0), Some(5), Some(0)));

    fs::remove_file(src.join("f0.txt")).unwrap();
    call(format!(r#"{{"cmd":"box_scan","box_id":{b},"path":"{p}"}}"#));
    let s = wait_done();
    assert_eq!((s.i64("unchanged"), s.i64("removed")), (Some(4), Some(1)));

    // 확장자 필터와 결과 목록 조회(box_scan_files)
    fs::write(src.join("a.HWPX"), "1").unwrap();
    fs::write(src.join("b.exe"), "2").unwrap();
    let ext_started = call(format!(r#"{{"cmd":"box_scan","box_id":{b},"path":"{p}","extensions":["hwpx",".TXT"]}}"#));
    assert_eq!(ext_started.bool("started"), Some(true));
    let s = wait_done();
    assert_eq!(s.i64("total"), Some(5), "txt 4개(f1~f3, 하위/g)+hwpx 1개, exe 제외");
    let listed = call(format!(r#"{{"cmd":"box_scan_files","box_id":{b},"path":"{p}","limit":100}}"#));
    assert_eq!(listed.bool("ok"), Some(true));
    let files = listed.arr("files").unwrap();
    assert_eq!(files.len(), 5);
    assert!(files.iter().all(|f| !f.str("path").unwrap().ends_with(".exe")));
    let page = call(format!(r#"{{"cmd":"box_scan_files","box_id":{b},"path":"{p}","offset":4,"limit":100}}"#));
    assert_eq!(page.arr("files").unwrap().len(), 1);
    assert_eq!(call(r#"{"cmd":"box_scan_files"}"#.into()).bool("ok"), Some(false));
}

#[test]
fn test_nb_source_from_item_reuse_and_back_link() {
    let ctx = TestContext::new("nb_item_link");
    let db = Arc::new(Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap()));
    let running = Arc::new(AtomicBool::new(true));
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let nb = call(r#"{"cmd":"nb_create","name":"노트"}"#.into()).i64("id").unwrap();
    let md = ctx.dir.join("계획.md");
    fs::write(&md, "# 추진 계획\n본문\n").unwrap();
    let b = db.lock().unwrap().box_create("자료함", "").unwrap();
    let item = db.lock().unwrap().item_add(b, "file", md.to_str().unwrap(), "계획.md", "basis", 0.0, 0.0, None).unwrap();

    // 처음 추가하면 새 출처, 다시 추가하면 같은 출처를 재사용한다.
    let first = call(format!(r#"{{"cmd":"nb_source_from_item","notebook_id":{nb},"item_id":{item}}}"#));
    assert_eq!(first.bool("ok"), Some(true), "{first:?}");
    assert_eq!(first.bool("reused"), Some(false));
    let sid = first.i64("id").unwrap();
    let again = call(format!(r#"{{"cmd":"nb_source_from_item","notebook_id":{nb},"item_id":{item}}}"#));
    assert_eq!(again.i64("id"), Some(sid));
    assert_eq!(again.bool("reused"), Some(true));
    let list = call(format!(r#"{{"cmd":"nb_source_list","notebook_id":{nb}}}"#));
    assert_eq!(list.arr("sources").unwrap().len(), 1);
    assert_eq!(list.arr("sources").unwrap()[0].i64("item_id"), Some(item));

    // 출처 → 원본 항목 조회.
    let back = call(format!(r#"{{"cmd":"nb_source_item","notebook_id":{nb},"source_id":{sid}}}"#));
    assert_eq!(back.bool("found"), Some(true), "{back:?}");
    assert_eq!(back.i64("item_id"), Some(item));
    assert_eq!(back.i64("box_id"), Some(b));

    // 직접 추가한 출처는 연결이 없고, 항목을 지우면 found:false, 없는 항목·노트북은 오류.
    let md2 = ctx.dir.join("직접.md");
    fs::write(&md2, "본문\n").unwrap();
    let p2 = md2.to_str().unwrap().replace(std::path::MAIN_SEPARATOR, "/");
    let direct = call(format!(r#"{{"cmd":"nb_source_add","notebook_id":{nb},"source_path":"{p2}"}}"#)).i64("id").unwrap();
    let none = call(format!(r#"{{"cmd":"nb_source_item","notebook_id":{nb},"source_id":{direct}}}"#));
    assert_eq!(none.bool("found"), Some(false));
    call(format!(r#"{{"cmd":"item_delete","id":{item}}}"#));
    let gone = call(format!(r#"{{"cmd":"nb_source_item","notebook_id":{nb},"source_id":{sid}}}"#));
    assert_eq!(gone.bool("found"), Some(false));
    assert_eq!(call(format!(r#"{{"cmd":"nb_source_from_item","notebook_id":{nb},"item_id":99999}}"#)).bool("ok"), Some(false));
    assert_eq!(call(format!(r#"{{"cmd":"nb_source_from_item","notebook_id":99999,"item_id":1}}"#)).bool("ok"), Some(false));
}

#[test]
fn test_nb_source_item_column_migration_on_old_db() {
    let ctx = TestContext::new("nb_item_migrate");
    let path = ctx.dir.join("library.db");
    {
        let db = Database::open(path.to_str().unwrap()).unwrap();
        drop(db);
    }
    // item_id 열이 없는 옛 nb_source 표를 흉내 낸 뒤 다시 열어도 열이 생긴다.
    let c = rusqlite::Connection::open(&path).unwrap();
    c.execute_batch("DROP INDEX IF EXISTS idx_nb_source_item; ALTER TABLE nb_source DROP COLUMN item_id;").unwrap();
    drop(c);
    let db = Database::open(path.to_str().unwrap()).unwrap();
    let has: bool = db.connection().query_row("SELECT EXISTS(SELECT 1 FROM pragma_table_info('nb_source') WHERE name='item_id')", [], |r| r.get(0)).unwrap();
    assert!(has);
}

/// 메모 편집기(edit_*) 명령이 파이프 처리기에서 editor_core로 위임되는지: Flutter KlibEditorCore가 보내는 순서 그대로.
#[test]
fn test_edit_commands_delegate_to_editor_core() {
    let ctx = TestContext::new("edit_cmds");
    let db = Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap());
    let running = AtomicBool::new(true);
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let ok = |v: &json::Value| assert_eq!(v.bool("ok"), Some(true), "응답 실패: {:?}", v.str("message"));

    let pong = call(r#"{"cmd":"edit_ping"}"#.into());
    ok(&pong);
    assert_eq!(pong.str("message"), Some("pong"));

    let opened = call(r#"{"cmd":"edit_open","text":"가나\r\n다"}"#.into());
    ok(&opened);
    let doc = opened.i64("doc").unwrap();
    assert_eq!(opened.str("line_ending"), Some("CRLF"));
    assert_eq!(opened.str("encoding"), Some("UTF-8"));
    assert_eq!(opened.i64("lines"), Some(2));

    // 한글 조합: 같은 구간 교체가 한 번의 실행취소 묶음이 된다("가나\n다" 끝 = 10바이트).
    for (s, e, t) in [(10, 10, "ㅎ"), (10, 13, "하"), (10, 13, "한")] {
        ok(&call(format!(r#"{{"cmd":"edit_replace","doc":{doc},"start":{s},"end":{e},"text":"{t}"}}"#)));
    }
    let text = call(format!(r#"{{"cmd":"edit_text","doc":{doc}}}"#));
    assert_eq!(text.str("text"), Some("가나\n다한"));
    let undo = call(format!(r#"{{"cmd":"edit_undo","doc":{doc}}}"#));
    ok(&undo);
    assert_eq!(undo.bool("changed"), Some(true));
    assert_eq!(call(format!(r#"{{"cmd":"edit_text","doc":{doc}}}"#)).str("text"), Some("가나\n다"));
    let redo = call(format!(r#"{{"cmd":"edit_redo","doc":{doc}}}"#));
    assert_eq!(redo.i64("cursor"), Some(13));

    // 찾기·모두 바꾸기·서식·상태값·줄 조회.
    let found = call(format!(r#"{{"cmd":"edit_find","doc":{doc},"query":"다","from":0}}"#));
    assert_eq!((found.bool("found"), found.i64("start"), found.i64("end")), (Some(true), Some(7), Some(10)));
    let all = call(format!(r#"{{"cmd":"edit_replace_all","doc":{doc},"query":"가","with":"카"}}"#));
    assert_eq!(all.i64("count"), Some(1));
    let bold = call(format!(r#"{{"cmd":"edit_md_inline","doc":{doc},"start":0,"end":6,"kind":"bold"}}"#));
    ok(&bold);
    assert_eq!(call(format!(r#"{{"cmd":"edit_lines","doc":{doc},"from":0,"to":1}}"#)).arr("lines").unwrap()[0].str("text"), Some("**카나**"));
    let lc = call(format!(r#"{{"cmd":"edit_line_col","doc":{doc},"pos":5}}"#));
    assert_eq!((lc.i64("line"), lc.i64("col")), (Some(1), Some(4)));
    let info = call(format!(r#"{{"cmd":"edit_info","doc":{doc}}}"#));
    assert_eq!(info.i64("chars"), Some(9));
    assert_eq!(info.bool("dirty"), Some(true));

    // 저장(원래 CRLF로) 후 닫기. 닫은 문서는 오류.
    let path = ctx.dir.join("memo.md");
    let p = path.to_str().unwrap().replace('\\', "/");
    ok(&call(format!(r#"{{"cmd":"edit_save","doc":{doc},"path":"{p}"}}"#)));
    assert_eq!(fs::read(&path).unwrap(), "**카나**\r\n다한".as_bytes());
    ok(&call(format!(r#"{{"cmd":"edit_close","doc":{doc}}}"#)));
    let gone = call(format!(r#"{{"cmd":"edit_info","doc":{doc}}}"#));
    assert_eq!(gone.bool("ok"), Some(false));
    assert!(gone.str("message").unwrap().contains("찾을 수 없습니다"));

    // 알 수 없는 edit_ 명령은 코어의 오류로, 다른 명령은 기존 처리 그대로.
    assert_eq!(call(r#"{"cmd":"edit_nope"}"#.into()).bool("ok"), Some(false));
    assert_eq!(call(r#"{"cmd":"ping"}"#.into()).str("message"), Some("pong"));
}

#[test]
fn test_item_text_get_set_for_memo_editor() {
    let ctx = TestContext::new("item_text");
    let db = Mutex::new(Database::open(&ctx.dir.join("library.db").to_str().unwrap()).unwrap());
    let running = AtomicBool::new(true);
    let call = |req: String| json::parse(&pipe::handle_request(&req, &db, &running)).unwrap();
    let ok = |v: &json::Value| assert_eq!(v.bool("ok"), Some(true), "응답 실패: {:?}", v.str("message"));

    let bid = call(r#"{"cmd":"box_create","name":"메모함"}"#.into()).i64("id").unwrap();
    let added = call(format!(r#"{{"cmd":"item_add","box_id":{bid},"kind":"text","display_name":"회의","space":"core","content":"첫 줄\n둘째 줄"}}"#));
    ok(&added);
    let iid = added.i64("id").unwrap();

    // 읽기: 사본 내용과 이름이 온다.
    let got = call(format!(r#"{{"cmd":"item_text_get","id":{iid}}}"#));
    ok(&got);
    assert_eq!(got.str("content"), Some("첫 줄\n둘째 줄"));
    assert_eq!(got.str("display_name"), Some("회의"));
    assert_eq!(got.str("kind"), Some("text"));

    // 고치기: 내용과 이름을 바꾸고, 사본 경로는 그대로, 임시 파일은 남지 않는다.
    let before = db.lock().unwrap().item_get(iid).unwrap().unwrap().source_path;
    let set = call(format!(r###"{{"cmd":"item_text_set","id":{iid},"display_name":"회의 정리","content":"# 결론\n**예산** 확정"}}"###));
    ok(&set);
    assert_eq!(set.str("display_name"), Some("회의 정리"));
    let row = db.lock().unwrap().item_get(iid).unwrap().unwrap();
    assert_eq!(row.source_path, before);
    assert_eq!(row.display_name, "회의 정리");
    assert_eq!(fs::read_to_string(&row.source_path).unwrap(), "# 결론\n**예산** 확정");
    let dir = Path::new(&row.source_path).parent().unwrap();
    assert_eq!(fs::read_dir(dir).unwrap().count(), 1, "임시 파일이 남았습니다");
    assert_eq!(call(format!(r#"{{"cmd":"item_text_get","id":{iid}}}"#)).str("content"), Some("# 결론\n**예산** 확정"));

    // 이름을 비우면 이름은 그대로 두고 내용만 고친다.
    ok(&call(format!(r#"{{"cmd":"item_text_set","id":{iid},"display_name":"  ","content":"다시"}}"#)));
    assert_eq!(db.lock().unwrap().item_get(iid).unwrap().unwrap().display_name, "회의 정리");

    // 거절: content 없음, 없는 항목, 파일 항목, 자료함 데이터 폴더 밖을 가리키는 글 항목.
    assert_eq!(call(format!(r#"{{"cmd":"item_text_set","id":{iid}}}"#)).bool("ok"), Some(false));
    assert_eq!(call(r#"{"cmd":"item_text_get","id":999999}"#.into()).bool("ok"), Some(false));
    let outside = ctx.dir.join("원본.txt");
    fs::write(&outside, "사용자 원본").unwrap();
    let op = outside.to_str().unwrap().replace('\\', "/");
    let file_item = call(format!(r#"{{"cmd":"item_add","box_id":{bid},"kind":"file","source_path":"{op}","display_name":"원본.txt","space":"core"}}"#));
    ok(&file_item);
    let fid = file_item.i64("id").unwrap();
    let refused = call(format!(r#"{{"cmd":"item_text_set","id":{fid},"content":"덮어쓰기"}}"#));
    assert_eq!(refused.bool("ok"), Some(false));
    assert!(refused.str("message").unwrap().contains("글 자료"));
    let nid = call(format!(r#"{{"cmd":"item_add","box_id":{bid},"kind":"note","display_name":"메모","space":"core","content":"y"}}"#)).i64("id").unwrap();
    // DB를 직접 바꿔 사본 경로를 사용자 원본으로 돌려 놓아도 편집기는 거절한다.
    let raw = rusqlite::Connection::open(ctx.dir.join("library.db")).unwrap();
    raw.execute("UPDATE item SET source_path = ?1 WHERE id = ?2", rusqlite::params![outside.to_str().unwrap(), nid]).unwrap();
    let escaped = call(format!(r#"{{"cmd":"item_text_set","id":{nid},"content":"덮어쓰기"}}"#));
    assert_eq!(escaped.bool("ok"), Some(false));
    assert!(escaped.str("message").unwrap().contains("데이터 폴더 밖"));
    assert_eq!(fs::read_to_string(&outside).unwrap(), "사용자 원본");
}
