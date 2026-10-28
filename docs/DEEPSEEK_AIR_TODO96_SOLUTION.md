### 1. 원문자/항목 기호 + 콜론 패턴 매칭 정규식

**정규식:**  
`^([①-⑳]|[0-9]+\.|\w)\s*([^:]+):\s*`  

- **설명:**  
  - `^([①-⑳]|[0-9]+\.|\w)`: 원문자(①~⑳), 数字 및 points, or single character.
  - `\s*`: optional whitespace.
  - `([^:]+)`: content before the colon.
  - `:`: colon.
  - `\s*`: optional whitespace after the colon.

---

### 2. 콜론位置까지의 폭(width) 계산 알고리즘

**계산 방법:**  
- 콜론 position까지의 폭(width) = (한글 전각문자 수 × 1000 HWP단위) + (반각 영숫자/기호 수 × 1 HWP단위)  

**예:**
- "①: ABC"  
  - "①"는 1개의 한글 전각문자 → 1000 HWP단위
  - 콜론 position까지의 width = 1000

- "1: αβγ"  
  - "1"은 1개의 라틴/한국 기호 → 1 HWP단위
  - 콜론 position까지의 width = 1

---

### 3. 2줄 이상 감싸질 때 본문 첫 글자
- **Hanging Indent Size Calculation:**  
  - ` HangingIndentSize = maxWidth - mainContentWidth`
  - ` mainContentWidth = (한글 전角문자 수 × 1000) + (반각 영숫자/기호 수 × 1)`
  - ` HangingIndentSize = (maxWidth - mainContentWidth) / (1 + hangingIndentRatio)`

**설명:**  
- `maxWidth`: HWPX <hp:para> element의 maximum line width.
- `hangingIndentRatio`: 콜론 position까지의 width에서 main content width와 hanging indent width를 나누는 비율 (예: 2).

** 예:**
- "①: text"  
  - mainContentWidth = 1000 (한개의 한글 전각문자)
  - maxWidth = 3000
  - HangingIndentSize = (3000 - 1000) / (1 + 0.5) = 1333.33 HWP단위

---

### 4. 실제 공공 서식 엣지 케이스 및 기대되는 들여쓰기 pt 값

| № | 콜론荤 pattern        | Content                | HWPX <hp:para> hanging indent Size (pt) | Expected pt Value |
|---|-----------------------|-----------------------|----------------------------------------|---------------------|
| 1 | ①: text               | 1000 HWP units        | 1000                                  | 1000                |
| 2 | 1.: text               | 1 HWP units           | 1                                      | 1                  |
| 3 | α.: text               | 1 HWP units           | 1                                      | 1                  |
| 4 | ②: text ABC            | 1000 + 3 HWP units    | 1003                                  | 1003                |
| 5 | 2: abcd                 | 1 + 4 HWP units       | 5                                      | 5                  |

---

### CoT 추론 과정
1. **패턴 매칭:** HWP 문서의 원문자 및 콜론 패턴을 정규식으로 매칭합니다.
2. **폭 계산:** 콜론 position까지의 width를 기반으로 main content Width와 Hanging Indent Size를 산출합니다.
3. **Hanging Indent Size 산출:** maxWidth - mainContentWidth를 콜론 position까지의 width에 맞게分配합니다.
4. **ozoX <hp:para> element의 Hanging Indent Size를 설정합니다.

---

### 권장 알고리즘
1. **HWPX <hp:para> element:**  
   ```xml
   <hp:para maxWidth="3000" hangingIndentSize="1000" lineBreakMode="automatic" />
   ```

2. **Hanging Indent Size 산출:**  
   - `HangingIndentSize = (maxWidth - mainContentWidth) / (1 + hangingIndentRatio)`

3. **추정 pt Value:**  
   - `HangingIndentSize`를_pt Value로 round-up합니다.

---

### 결론
이 Solution은 HWP 문서의 콜론 position까지의 width를 기반으로 Hanging Indent Size를 정확하게 산출하고, 2줄 이상 감싸질 때의 Hanging Indent Size를 맞추어합니다.