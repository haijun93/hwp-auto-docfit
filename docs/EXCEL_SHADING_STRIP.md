# 엑셀 표 붙여넣기: 셀 배경 음영만 제거 (카드 XLSHADE)

## 무엇을 하나
`docfit_core/excel_html_shading.py`의 `strip_cell_shading(data)`가 엑셀 클립보드 `HTML Format`(CF_HTML, bytes·str)에서
**셀 배경 음영만** 지운 같은 형식의 값을 돌려준다. `strip_cell_shading_report(data)`는 `(결과, {changed, removed, reason})`을 준다.

| 지움 | 보존 |
|---|---|
| `td/th/tr/col/colgroup/table/tbody/thead/tfoot`의 `bgcolor`·`background` 속성 | 글자색(`color`)·글꼴·굵기·정렬 |
| 같은 태그 인라인 `style`의 `background*`·`mso-pattern`·`mso-background-source` | 테두리(`border*`)·`colspan`/`rowspan`·`<col width>`·표 구조 |
| `<style>` 규칙(`td {…}`, `.xl63 {…}`)의 같은 선언 | 글자 내용, `<span>` 등 셀 안쪽 태그의 style, `mso-number-format` |

CF_HTML 머리의 `StartHTML/EndHTML/StartFragment/EndFragment`는 새 본문에 맞춰 같은 자릿수로 다시 계산한다.

## 안전한 폴백
다음이면 **원본 객체를 그대로** 돌려준다: 빈 값·문자열/바이트 아님, UTF-8 복호화 실패, 표 셀(`<td>/<th>`) 없음,
지울 음영 없음, 예외 발생, 변환 전후 검증 실패(구조 태그·병합·클래스·글자·`color`/`border` 선언·글자 내용 중 하나라도 달라짐).

## 서비스 명령
`ExcelTableService.command('strip_shading')` — 클립보드 HTML을 읽어 변환하고, 바뀐 경우에만 같은 클립보드에
HTML Format(+원래 글자 TSV)을 다시 쓴다. 바꿀 것이 없거나 폴백이면 클립보드를 건드리지 않는다.
화면·kagent 연결은 하지 않았다. 기존 `paste_clean`(모델 → HWPX 경로)과는 별개다.

## 한계
- 배경을 지우면 **흰 글자 + 짙은 배경** 셀은 흰 바탕에 흰 글자가 되어 안 보인다(글자색 보존 원칙 때문). 필요하면 후속으로 밝은 글자색을 검은색으로 바꾸는 옵션을 둔다.
- `<span>`·`<font>` 등 셀 안쪽 태그의 배경(글자 강조)은 "셀 배경"이 아니므로 지우지 않는다.
- 조건부 서식·표 스타일로 칠해진 색도 엑셀이 HTML에 인라인/클래스로 풀어 주므로 지워진다. 그러나 이미지(`background` URL 그림)는 같은 속성이라 함께 지워진다.
- 선택자 규칙은 `{…}` 단순 규칙만 다룬다(중첩·`@media` 미지원). 엑셀은 이 형태만 만든다.
- 실제 한/글 붙여넣기 결과는 Windows·한/글 실기기에서 확인하지 못했다(COM 금지 조건). 합성 샘플(`tests/fixtures/xlshade_*.cf_html`)과 기존 실제 샘플로만 검증했다.
