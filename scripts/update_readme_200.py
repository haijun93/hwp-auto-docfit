import re

def update_readme(path, is_github=False):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Update download URLs and badges
    text = text.replace('v1.80.15', 'v2.0.0')
    text = text.replace('HWP_AutoDocFit_v1.80.15', 'HWP_AutoDocFit_v2.0.0')

    # Update release header
    old_header = '<h2 align="center">새로워진 v2.0.0</h2>'
    new_section = '''<h2 align="center">새로워진 v2.0.0 메이저 릴리즈</h2>
<p align="center">차세대 통합 단일 셸(Flutter 6-Tab) 안착, 한글 타이포그래피 정밀 조판(표 줄간격 100%·자간 -25%, 원문자 콜론 정렬), 공공 표준 표 6대 템플릿 탑재</p>

### 차세대 통합 단일 셸 워크스페이스 (Flutter 6-Tab) (2.0.0)

6개 핵심 작업 도구(자간/행간 맞춤, 표 단위 서식, 표그림판, 다이어그램, 마인드맵, 공공도구함)가 하나의 단일 창 안에서 탭 전환으로 매끄럽게 연결됩니다. 탭 전환 시 창 닫기 보호 장치(CloseGuards)를 분리하여 백그라운드 작업 손실 없이 신속하게 화면을 넘나들 수 있습니다.

### 표 셀 줄간격 최소 100% 및 자간 -25% 보장 (TODO 76~82) (2.0.0)

표 안의 글자가 위아래로 답답하게 겹치지 않도록 줄간격을 최소 100%로 보장하고, 자간을 최소 -25%까지 조절하여 가독성을 극대화했습니다. 구형 20자 분기 휴리스틱을 전면 폐기하여 모든 표 칸에서 균일하고 단정한 조판 품질을 제공합니다.

### 원문자·항목기호 콜론 후속 자동 들여쓰기 정렬 (TODO 96) (2.0.0)

원문자(`①~⑳`), 번호(`1.`), 한글 기호 뒤에 콜론(`:`, `：`)이 오는 문단(`①사업목적:인공지능`)에서 둘째 줄 이상의 후속 문장이 콜론 뒤 본문 첫 글자에 수직으로 칼같이 일치하도록 자동 들여쓰기(Hanging Indent) 메트릭스를 적용했습니다.

### 플로우차트 네이티브 한글 도형 클립보드 복사 (TODO 164~168) (2.0.0)

다이어그램 및 흐름도 편집기에서 작성한 사각형, 타원, 화살표 연결선을 비트맵 이미지가 아닌 실제 한/글 고유의 네이티브 벡터 도형(`hp:rect`, `hp:ellipse`, `hp:connectLine`)으로 한/글에 즉시 붙여넣을 수 있습니다.

### 공공기관 행정 보고서 표준 표 6대 템플릿 탑재 (2.0.0)

행정안전부 및 기획재정부 보고서 지침을 준수한 6대 표준 표(요약 1칸 표, 2열 정의 표, 3~4열 비교 표, 간트차트 일정표, 예산 산출 표, Q&A 체크리스트 표) 정밀 메트릭스 및 프리셋이 탑재되었습니다.

---

<h2 align="center">이전 릴리즈 (v1.80.15)</h2>'''

    text = text.replace(old_header, new_section, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'[OK] Successfully updated {path}')

update_readme(r'C:\HWP_AUTODOCFIT\v1803\v2\README.md')
update_readme(r'C:\HWP_AUTODOCFIT\v1803\v2\.github\README.md', is_github=True)
