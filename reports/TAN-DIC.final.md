# TAN-DIC 결과 보고서

## 결론

`lindera-ko-dic 0.38.1`의 `build.rs`는 `LINDERA_CACHE` 환경변수가 있어도 다운로드 URL을 호출합니다. 캐시 경로는 빌드된 사전의 재사용 경로이며 원본 tarball 입력이나 URL 교체 기능은 제공하지 않아, 미러 tarball 다운로드만으로 네트워크 의존을 제거할 수 없습니다. 우선순위 2 방식으로 ko-dic을 선택 기능으로 분리했습니다.

## 변경 사항

- klib 기본 feature에서 `lindera` 및 `lindera-tantivy`의 `ko-dic`을 비활성화하고, 필요할 때 `--features ko-dic`으로 켤 수 있도록 했습니다.
- 기본 본문 검색 필드는 bigram tokenizer를 사용합니다. 기존 초성 검색, 자모 기반 오타 검색, 동의어 확장은 유지됩니다.
- ko-dic feature가 켜진 경우에만 Lindera 사전을 로드하고 형태소 tokenizer를 등록합니다. 이 feature로 빌드하면 Lindera upstream의 CloudFront 다운로드 의존성이 남습니다.
- Windows CI klib 단계에서 `%LOCALAPPDATA%/DocFitTools/mingw64/bin`이 존재하면 PATH 앞에 추가하도록 했습니다.
- 기존 검색 코드의 Tantivy tokenizer API/reader API 컴파일 오류, UTF-8 손상 테스트 fixture, integration test의 검색 모듈 미연결을 정리해 전체 테스트를 실행 가능하게 했습니다.
- 의존성 버전 고정(`=0.38.1`)은 유지했고 lockfile 체크섬을 변경하지 않았습니다.

## 검증

실행 환경 PATH 앞에 `$env:LOCALAPPDATA/DocFitTools/mingw64/bin`을 추가한 뒤 실행:

```powershell
cargo test --manifest-path klib/Cargo.toml
```

결과: 성공. klib 단위 테스트 8개, 통합 테스트 23개 통과.

## 제한 사항

선택 기능 `ko-dic`은 기본 빌드에서 사용하지 않습니다. 해당 기능을 켜면 lindera upstream URL이 그대로 사용되므로 오프라인 빌드는 보장되지 않습니다. 기본 빌드에서는 bigram·초성·오타 검색으로 동작합니다.

## 커밋

요청에 따라 `feature/v4-tantivy` 브랜치에 커밋했으며 푸시는 수행하지 않았습니다.
