# 표 셀 그림 → 셀 배경 그림 변환 (HWPX/OWPML 조사 + 구현 메모)

> 상태: 순수 Python 변환 함수만 구현(`docfit_core/cell_image_bg.py`). 화면(카드) 연결은 이 카드 범위 밖.
> **한/글에서 실제 표시는 확인하지 못했다 — PC(Windows 한/글) 확인 필요.** 아래 XML 구조는 OWPML 명세와 저장소 코드 기준이며, 실제 한/글 저장본과 대조하지 않았다.

## OWPML 구조
| 항목 | 위치 | 비고 |
|---|---|---|
| 셀 | `hp:tbl/hp:tr/hp:tc` | 속성 `borderFillIDRef`가 셀 테두리/배경 참조. 병합 셀은 `hp:cellSpan colSpan/rowSpan`인 한 개의 `hp:tc` |
| 셀 안 그림 | `hp:tc/hp:subList/hp:p/hp:run/hp:pic` | 그림 데이터 참조는 `hp:pic` 안 `hc:img binaryItemIDRef="..."` |
| 테두리/배경 | `Contents/header.xml` → `hh:refList/hh:borderFills/hh:borderFill[@id]` | 자식: 테두리선들 + `hc:fillBrush` |
| 색 채우기 | `hc:fillBrush/hc:winBrush faceColor=...` | |
| 그림 채우기 | `hc:fillBrush/hc:imgBrush mode="TOTAL"` 안 `hc:img binaryItemIDRef bright contrast effect alpha` | `TOTAL`=크기에 맞추어 |
| 이미지 데이터 | `BinData/<id>.<확장자>` (+ `Contents/content.hpf` 목록) | `binaryItemIDRef`가 가리킴 |

## 변환 규칙
1. 대상: 글자 없음 + 셀 바로 안(하위 표 제외) `hp:pic` 정확히 1개 + 하위 표 없음. 글자+그림, 그림 여러 개, 글자만, 표 밖 그림은 그대로 둔다.
2. 셀의 기존 `borderFill`을 **복제**해 새 id(최대 id+1)를 주고 `fillBrush`를 `imgBrush`로 교체(테두리선 보존, 기존 색 채우기는 그림이 대신함). 기존 `borderFill`은 수정하지 않는다(다른 셀이 공유).
3. 셀 `borderFillIDRef`를 새 id로 바꾸고 `hp:pic` 삭제. 같은 `binaryItemIDRef`를 재사용하므로 `BinData`는 불변.
4. `borderFills@itemCnt` 갱신. 셀마다 새 항목을 만든다(같은 그림·테두리 중복 병합은 후속).
5. 파일 단위: `open_hwpx_safely`로 열고, header/section만 `batch_format._serialize`로 다시 써서 네임스페이스 접두사(`hp:` 등)를 보존. 나머지 항목은 바이트 동일. 변환할 셀이 없으면 파일을 그대로 복사. 두 번 실행해도 결과 동일(멱등).

## 알려진 한계 / PC 확인 필요
- 한/글에서 열었을 때 배경 그림이 보이는지, 셀 높이(그림이 글자처럼 셀을 키우던 경우)가 유지되는지 미확인.
- `imgBrush` 하위 속성값(`effect="REAL_PIC"` 등)과 `fillBrush` 안 자식 순서는 실제 한/글 저장본과 대조 필요.
- 셀 안 그림 앞뒤의 빈 `run`/문단은 남는다(높이 영향 가능).
- 글상자·도형 안 그림, 이미 `imgBrush`가 있는 셀 처리는 정의하지 않음.
