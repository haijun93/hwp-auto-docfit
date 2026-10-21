<h1 align="center">한글편집 후처리</h1>

<p align="center"><b>보고서 마무리. 버튼 하나로.</b></p>

<p align="center">
다 쓴 한글(HWP·HWPX) 보고서나 메모 한 장을 넣고 <b>「정리 시작」</b>만 누르세요.<br>
설치된 한/글을 직접 다뤄 공문서 모양으로 다듬어 드립니다. 원본은 그대로 둡니다.
</p>

<p align="center">
<a href="https://github.com/haijun93/hwp-auto-docfit/releases/download/v1.80.1/HWP_AutoDocFit_v1.80.1_Portable.exe"><img alt="무설치로 바로 받기" src="https://img.shields.io/badge/%E2%AC%87%20%EB%AC%B4%EC%84%A4%EC%B9%98%EB%A1%9C%20%EB%B0%94%EB%A1%9C%20%EB%B0%9B%EA%B8%B0-v1.80.1-2563eb?style=for-the-badge"></a>
<a href="https://github.com/haijun93/hwp-auto-docfit/releases/download/v1.80.1/HWP_AutoDocFit_v1.80.1_Setup.exe"><img alt="설치용 받기" src="https://img.shields.io/badge/%EC%84%A4%EC%B9%98%EC%9A%A9%20%EB%B0%9B%EA%B8%B0-Setup-0ea5e9?style=for-the-badge"></a>
</p>
<p align="center">
<img alt="무료" src="https://img.shields.io/badge/%EA%B0%80%EA%B2%A9-%EB%AC%B4%EB%A3%8C-16a34a">
<img alt="Windows 10·11" src="https://img.shields.io/badge/Windows-10%C2%B711-0078d4">
<img alt="한/글 2020" src="https://img.shields.io/badge/%ED%95%9C%2F%EA%B8%80-2020-0ea5e9">
<img alt="문서 외부 전송 없음" src="https://img.shields.io/badge/%EB%AC%B8%EC%84%9C-%EC%99%B8%EB%B6%80%20%EC%A0%84%EC%86%A1%20%EC%97%86%EC%9D%8C-64748b">
</p>

<p align="center">
<a href="docs/media/overview-demo.mp4"><img src="docs/media/overview-demo.gif" alt="한글편집 후처리 5분 시연 — 누르면 고화질 영상" width="860"></a><br>
<sub>▶ 누르면 5분 시연 영상(고화질)이 열립니다</sub>
</p>

---

<h2 align="center">새로워진 v1.80.1</h2>
<p align="center">기호가 무엇이든 위계대로. 둘째 줄까지 반듯하게. 그리고 더 안전하게.</p>

### 어떤 항목기호를 써도, 같은 공문서 모양으로.

`□ ㅇ -`만 알아듣던 시절은 끝났습니다. `1.` `1.1.` `1.1.1.`, `가.` `1)` `(1)`, `①`, `Ⅰ.` `A.` `a)`, `◆ ▶ ➢`, `■ ● ▪`, `▣ ✓ →`까지.
문서에 쓰인 기호의 **위계를 스스로 읽어 내** 1·2·3단계에 `□`·`ㅇ`·`-` 서식을 입힙니다. 기호 글자는 손대지 않습니다.

<p align="center"><img src="docs/media/v180/marker-schemes.png" alt="같은 보고서를 □ㅇ- 체계와 1. 1.1. 1.1.1. 체계로 썼을 때 같은 서식으로 정리된 결과" width="860"><br>
<sub>같은 내용을 서로 다른 기호로 써도, 글꼴·크기·굵기·내어쓰기가 똑같이 정리됩니다</sub></p>

<p align="center"><img src="docs/media/v180/decimal-before-after.png" alt="1. 1.1. 1.1.1. 번호로 쓴 메모의 적용 전과 후" width="860"><br>
<sub>번호로만 쓴 메모(왼쪽) → 단계별 서식이 입혀진 보고서(오른쪽)</sub></p>

### 둘째 줄은 언제나 본문 첫 글자에서.

`ㅇ (현황)`의 둘째 줄은 `(` 아래, `- 항세기`는 `항` 아래, `* 항세기:`는 콜론 뒤 첫 글자 아래.
한/글의 Shift+Tab을 그 자리에서 직접 실행해 **눈대중 없이** 맞춥니다. 붙임 번호 `2.`도 `1.` 바로 아래에 섭니다.

<p align="center"><img src="docs/media/v180/indent-before-after.png" alt="내어쓰기 적용 전과 후 — 둘째 줄이 본문 첫 글자에 맞춰짐" width="860"></p>

### 한 쪽 안의 줄 간격은 하나로. 빈 문서 저장은 원천 차단.

쪽에 맞추려고 줄 간격을 줄이면 **같은 쪽 전체를 같은 값으로** 맞춥니다(사용자 검수에서 나온 개선).
드물게 txt 입력이 빈 문서로 저장되던 문제를 고쳤고, 만에 하나 결과가 비면 성공으로 넘기지 않고 멈춥니다.

---

<h2 align="center">이렇게 달라집니다</h2>
<p align="center">움직이는 그림은 <b>적용 전 ↔ 적용 후</b>를 번갈아 보여 줍니다. <b>빨간색이 바뀌는 곳</b>입니다.</p>

### 갈라진 단어, 한 줄로.

`거점(지 / 구)`, `수 / 립하여`. 줄 끝에서 쪼개진 어절을 자간을 살짝 조절해 한 줄에 모읍니다. **본문 단어는 더하지도, 빼지도 않습니다.**

<table>
<tr>
<td width="50%" align="center"><img src="docs/media/anim/spacing.gif" alt="자간 정리 전후"><br><sub>적용 전 ↔ 후</sub></td>
<td width="50%" align="center"><a href="docs/media/features/spacing.png"><img src="docs/media/features/spacing.png" alt="실제 문서의 자간 정리 전후 비교"></a><br><sub>실제 보고서: 줄을 옮긴 어절을 빨간색으로 표시</sub></td>
</tr>
</table>

### 메모 한 장이, 보고서 한 부로.

텍스트 초안을 넣으면 제목·개요 표, 기호별 글꼴과 간격, 내어쓰기, 쪽 배치까지 **한 번에**.

<table>
<tr>
<td width="50%" align="center"><img src="docs/media/anim/all-in-one.gif" alt="한 번에 적용 전후"><br><sub>적용 전 ↔ 후</sub></td>
<td width="50%" align="center"><a href="docs/media/samchein/all-comparison.png"><img src="docs/media/samchein/all-comparison.png" alt="텍스트 초안과 완성된 보고서 비교"></a><br><sub>txt 초안(왼쪽) → 완성 보고서(오른쪽)</sub></td>
</tr>
</table>

### 내어쓰기, 둘째 줄까지 칼같이.

<table>
<tr>
<td width="50%" align="center"><img src="docs/media/anim/hanging-indent.gif" alt="내어쓰기 전후"><br><sub>항목기호 뒤 첫 글자에 맞춤</sub></td>
<td width="50%" align="center"><img src="docs/media/anim/hanging-indent-colon.gif" alt="콜론 라벨 내어쓰기 전후"><br><sub>콜론 라벨은 콜론 뒤 본문에 맞춤</sub></td>
</tr>
</table>

### 넘친 두 줄, 앞쪽으로 쏙.

<table>
<tr>
<td width="50%" align="center"><img src="docs/media/anim/page-fit.gif" alt="쪽 수 맞춤 전후"><br><sub>마지막 쪽 몇 줄을 앞쪽에 담기</sub></td>
<td width="50%" align="center"><img src="docs/media/anim/page-group.gif" alt="쪽 묶음 전후"><br><sub>제목만 쪽 끝에 홀로 남지 않게</sub></td>
</tr>
</table>

### 우리 기관 서식, 그대로 복사.

예시 보고서 한 부를 끌어다 놓으면 그 모양을 배웁니다. 제각각인 문서는 같은 역할끼리 **다른 것만** 골라 고칩니다.

<table>
<tr>
<td width="50%" align="center"><img src="docs/media/anim/format-copy.gif" alt="서식 복사 전후"><br><sub>예시 보고서 서식 복사</sub></td>
<td width="50%" align="center"><img src="docs/media/anim/style-unify.gif" alt="서식 통일 전후"><br><sub>글꼴·크기·색 통일</sub></td>
</tr>
</table>

### 표도, 깔끔하게.

<table>
<tr>
<td width="33%" align="center"><img src="docs/media/anim/table-convert.gif" alt="표 변환 전후"><br><sub>┌─┐ 글자 그림 → 진짜 표</sub></td>
<td width="33%" align="center"><img src="docs/media/anim/table-width.gif" alt="표 너비 전후"><br><sub>칸 너비 자동 맞춤</sub></td>
<td width="33%" align="center"><img src="docs/media/anim/table-format.gif" alt="표 서식 전후"><br><sub>머리글·본문 서식</sub></td>
</tr>
</table>

### 자잘한 손질까지, 알아서.

<table>
<tr>
<td width="33%" align="center"><img src="docs/media/anim/short-line.gif" alt="짧은 줄 전후"><br><sub>몇 글자만 남은 줄 합치기</sub></td>
<td width="33%" align="center"><img src="docs/media/anim/spacing-rules.gif" alt="띄어쓰기 규칙 전후"><br><sub>쉼표·괄호·날짜 표기</sub></td>
<td width="33%" align="center"><img src="docs/media/anim/abbreviation.gif" alt="준말 전후"><br><sub>준말 → 제목·개요 표</sub></td>
</tr>
<tr>
<td align="center"><img src="docs/media/anim/labels.gif" alt="라벨 전후"><br><sub>문두 라벨 굵게</sub></td>
<td align="center"><img src="docs/media/anim/asterisk.gif" alt="별표 전후"><br><sub>별표 주석 위첨자</sub></td>
<td align="center"><img src="docs/media/anim/original-layout.gif" alt="원본 쪽 구성 전후"><br><sub>원본 쪽 구성 그대로</sub></td>
</tr>
</table>

---

<h2 align="center">직접 보세요</h2>

<table>
<tr>
<td width="50%" align="center"><a href="docs/media/samchein/spacing-guide.mp4"><img src="docs/media/samchein/spacing-guide.gif" alt="자간 정리 실제 처리 영상"></a><br><b>자간 정리</b><br><sub>파일 추가 → 자간 정리 → 결과 비교</sub></td>
<td width="50%" align="center"><a href="docs/media/samchein/all-guide.mp4"><img src="docs/media/samchein/all-guide.gif" alt="한 번에 적용 실제 처리 영상"></a><br><b>한 번에 적용</b><br><sub>txt 초안 → 완성 보고서</sub></td>
</tr>
</table>

---

<h2 align="center">숫자로 말합니다</h2>

<table>
<tr>
<td align="center" width="20%"><h3>약 21분</h3><sub>3쪽 보고서 한 건에서<br>아끼는 시간(쪽당 7분 손작업 추정)</sub></td>
<td align="center" width="20%"><h3>0건</h3><sub>34쪽 실제 취합 문서의<br>본문 글자 변형</sub></td>
<td align="center" width="20%"><h3>0건</h3><sub>서식 예시 3종을 복사해<br>다시 입혔을 때 서식 불일치</sub></td>
<td align="center" width="20%"><h3>10가지</h3><sub>□ㅇ-와 9가지 다른<br>항목기호 체계를 지원</sub></td>
<td align="center" width="20%"><h3>461개</h3><sub>기관 문서 30개의 표 중<br>사용자가 꾸민 표 오판 0건</sub></td>
</tr>
</table>

---

<h2 align="center">믿고 맡기세요</h2>

<table>
<tr>
<td width="25%" align="center"><h3>🗂</h3><b>원본은 그대로</b><br><sub>언제나 사본으로 작업하고<br>결과는 새 파일로 저장</sub></td>
<td width="25%" align="center"><h3>🔒</h3><b>내 PC 안에서만</b><br><sub>문서를 외부로 보내지 않습니다<br>기본은 폐쇄망 모드</sub></td>
<td width="25%" align="center"><h3>✅</h3><b>스스로 검사</b><br><sub>저장한 결과를 다시 열어<br>본문·표·그림 보존을 확인</sub></td>
<td width="25%" align="center"><h3>🛡</h3><b>꾸민 표는 손대지 않음</b><br><sub>장식 표·조직도·흐름표는<br>서식 작업에서 제외</sub></td>
</tr>
</table>

---

<h2 align="center">시작은 세 단계</h2>

<table>
<tr>
<td width="33%" align="center"><h3>① 넣기</h3>문서를 끌어다 놓기<br><sub>HWP·HWPX·txt·md·PDF</sub></td>
<td width="33%" align="center"><h3>② 고르기</h3><b>자간 정리</b> 또는 <b>한 번에 적용</b><br><sub>줄 끝만 / 보고서 모양까지</sub></td>
<td width="33%" align="center"><h3>③ 누르기</h3><b>정리 시작</b><br><sub>같은 폴더에 새 HWPX 저장</sub></td>
</tr>
</table>

<p align="center">처음이라면 함께 들어 있는 <b>「보고서 예시 파일(한번에 적용).txt」</b>로 5분 만에 체험해 보세요 — <a href="docs/USER_GUIDE.md#examples">따라 하기</a></p>

---

<h2 align="center">받기</h2>

| 파일 | 용도 |
|---|---|
| **[포터블 · HWP_AutoDocFit_v1.80.1_Portable.exe](https://github.com/haijun93/hwp-auto-docfit/releases/download/v1.80.1/HWP_AutoDocFit_v1.80.1_Portable.exe)** | 설치 없이 바로 실행 |
| [설치용 · HWP_AutoDocFit_v1.80.1_Setup.exe](https://github.com/haijun93/hwp-auto-docfit/releases/download/v1.80.1/HWP_AutoDocFit_v1.80.1_Setup.exe) | 시작 메뉴 등록, Windows 앱 제거로 정리 |
| [SHA256SUMS](https://github.com/haijun93/hwp-auto-docfit/releases/download/v1.80.1/SHA256SUMS) | 내려받은 파일 확인용 해시 |

- **필요한 것**: Windows 10·11(64비트), 문서를 편집할 수 있는 **한컴오피스 한/글**(2020에서 검증). Python 등 다른 설치는 필요 없습니다.
- 변환 엔진은 실행 파일에 들어 있습니다. 첫 실행 때 `C:\HWP_AUTODOCFIT`(쓰기 권한이 없으면 `%LOCALAPPDATA%\HwpAutoDocFit`)에 풀며, 인터넷에서 받지 않습니다.
- [전체 릴리스](https://github.com/haijun93/hwp-auto-docfit/releases/latest) · [v1.80.1 변경 사항](releases/v1.80.1.md) · [GitHub](https://github.com/haijun93/hwp-auto-docfit) · [GitLab](https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit)

---

<h2 align="center">자주 묻는 질문</h2>

<details><summary><b>정말 무료인가요?</b></summary>

네. 받아서 바로 쓰면 됩니다. 결제도, 회원 가입도 없습니다.
</details>

<details><summary><b>문서가 밖으로 나가지 않나요?</b></summary>

나가지 않습니다. 내 PC에 설치된 한/글을 직접 다뤄 처리합니다. 기본은 폐쇄망 모드라 앱이 스스로 외부에 접속하지 않습니다.
</details>

<details><summary><b>원본이 망가지면 어떡하죠?</b></summary>

원본은 열기만 하고 고치지 않습니다. 결과는 같은 폴더에 `(일괄적용)`·`(자간조정)` 같은 이름의 새 HWPX로 저장됩니다.
</details>

<details><summary><b>우리 기관 양식에도 맞출 수 있나요?</b></summary>

예시 보고서(HWP·HWPX·PDF)를 끌어다 놓으면 그 서식을 배웁니다. 이후에는 썸네일로 골라 쓰면 됩니다. 예시에 쓰인 항목기호가 `1.1.`이든 `◆`든 위계를 읽어 냅니다.
</details>

<details><summary><b>저희는 □ ㅇ - 대신 다른 기호를 써요.</b></summary>

괜찮습니다. 번호(`1.` `1.1.` `1-1` `가.` `1)` `(1)` `①`), 로마자·영문(`Ⅰ.` `A.` `a)`), 도형(`◆ ▶ ■ ● ✓ →` 등) 어떤 체계든 위계를 읽어 단계에 맞는 서식을 입힙니다. 기호 글자는 그대로 둡니다.
</details>

<details><summary><b>줄 간격은 건드리지 않았으면 해요.</b></summary>

한 번에 적용 카드의 **줄 간격 적용**을 끄면 문서의 줄 간격을 그대로 둡니다.
</details>

---

<h2 align="center">더 알아보기</h2>

<p align="center">
<a href="docs/USER_GUIDE.md"><b>자세한 사용 설명서</b></a> — 기능별 사용법·옵션·결과 파일·문제 해결<br>
<a href="releases/v1.80.1.md">v1.80.1 변경 사항</a> · <a href="HANDOVER.md">개발 인수인계 문서</a> · <a href="THIRD_PARTY_NOTICES.md">사용한 오픈소스</a> · <a href="LICENSE">라이선스</a>
</p>
