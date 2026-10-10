"""README용 기능 전후 도해를 재생성한다. 실제 앱 화면이나 실측 결과가 아니다.

중괄호로 둘러싼 글자만 빨간색으로 그린다. 위치·모양·내용 변경을 구분하며
사용자 문서는 읽지 않는다. 실행: python scripts/build_readme_comparisons.py
실제 사례 기록이 있는 자간 정리·한 번에 적용 이미지는 덮어쓰지 않는다.
"""
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/media/features'
INK = '#243247'
RED = '#c62828'
GRAY = '#64748b'
FONT_DIR = Path('C:/Windows/Fonts')


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ('malgunbd.ttf' if bold else 'malgun.ttf')), size)


def rich(draw, x, y, value, size=29, bold=False):
    for part in re.split(r'(\{[^{}]*\})', value):
        if not part:
            continue
        changed = part.startswith('{') and part.endswith('}')
        text = part[1:-1] if changed else part
        draw.text((x, y), text, font=font(size, bold), fill=RED if changed else INK)
        x += draw.textlength(text, font=font(size, bold))
    return x


def line(text, x=0, size=29, bold=False):
    return {'text': text, 'x': x, 'size': size, 'bold': bold}


def card(name, title, before, after, note, kind='lines'):
    return dict(name=name, title=title, before=before, after=after, note=note, kind=kind)


CARDS = [
    card('spacing', '자간·장평 조정 | 갈라진 어절을 한 줄로',
         [line('ㅇ 민원 대응 계획을 {수}'), line('{립하여} 추진합니다.', 25),
          line('ㅇ 현장 점검은 {담당}'), line('{부서}와 함께 진행합니다.', 25)],
         [line('ㅇ 민원 대응 계획을 {수립하여}'), line('   추진합니다.', 25),
          line('ㅇ 현장 점검은'), line('{담당부서}와 함께 진행합니다.', 25)],
         '빨간 어절의 줄 위치가 바뀝니다. 상황에 따라 앞줄 또는 뒷줄로 모읍니다.'),
    card('short-line', '짧은 마지막 줄 당기기 | 남은 글자를 앞줄로',
         [line('ㅇ 안내 자료를 배포'), line('{합니다.}', 25), line('마지막 줄: 4글자', size=25)],
         [line('ㅇ 안내 자료를 배포{합니다.}'), line('마지막 줄이 앞줄에 합쳐짐', size=25)],
         '예시는 기준을 4글자 이하로 설정한 경우입니다. 실행 기준은 설정에서 바꿉니다.'),
    card('hanging-indent', '내어쓰기 | 둘째 줄부터 본문 시작에 맞춤',
         [line('ㅇ (대상) 주민 대상 교육을'), line('{실시하고 참여 결과를}'), line('{정리하여 공유합니다.}')],
         [line('ㅇ (대상) 주민 대상 교육을'), line('{실시하고 참여 결과를}', 135),
          line('{정리하여 공유합니다.}', 135)],
         '빨간 줄의 시작 위치만 이동합니다. 기본은 라벨 뒤 본문, 사용자 서식은 해당 규칙을 따릅니다.'),
    card('page-fit', '쪽 수 맞춤 | 마지막 쪽에 조금 남은 글을 당김',
         [], [], '문단 간격 등을 조정해 당길 수 있는 경우의 예시입니다. 모든 문서를 한 쪽 줄이지는 않습니다.', 'page-fit'),
    card('page-group', '관련 문단 쪽 배치 | 제목과 내용을 함께',
         [], [], '제목·본문·표·주석을 묶어 배치합니다. 한 쪽보다 긴 묶음은 나누어질 수 있습니다.', 'page-group'),
    card('style-unify', '서식 통일 | 같은 역할의 문장끼리 맞춤',
         [line('ㅇ 교육을 실시합니다.'), line('ㅇ 결과를 공유합니다.'),
          line('ㅇ {자료를 배포합니다.}', size=23), line('다른 글자 크기: 12pt', size=25)],
         [line('ㅇ 교육을 실시합니다.'), line('ㅇ 결과를 공유합니다.'),
          line('ㅇ {자료를 배포합니다.}'), line('같은 역할의 대표값: 15pt', size=25)],
         '빨간 문장의 서식만 맞춥니다. 대표값을 확정할 근거가 있어야 교정합니다.'),
    card('all-in-one', '한 번에 적용 | 초안을 보고서 모양으로',
         [line('{제목1: 주민 교육 계획}'), line('{개요: 교육 운영 및 결과 공유}'),
          line('{ㅁ 추진 계획}'), line('{ㅇ 교육을 실시합니다.}', size=24)],
         [line('{주민 교육 계획}', size=35, bold=True), line('{교육 운영 및 결과 공유}'),
          line('{□ 추진 계획}', bold=True), line('{ㅇ 교육을 실시합니다.}')],
         '빨간 글자는 내용·기호·모양이 바뀌는 예시입니다. 제목·개요는 실제로 서식 표를 생성합니다.'),
    card('supplement', '부연설명 정렬 | 주석을 부모 문단에 맞춤',
         [line('ㅇ 교육을 실시합니다.'), line('{* 사전 신청자에 한함}'),
          line('{** 일정은 별도 안내}', 65), line('{※ 문의: 담당 부서}')],
         [line('ㅇ 교육을 실시합니다.'), line('{* 사전 신청자에 한함}', 65),
          line('{** 일정은 별도 안내}', 49), line('{※ 문의: 담당 부서}', 49)],
         '빨간 주석의 앞 빈칸을 부모 기호별 기준에 맞춥니다. **의 둘째 별표도 함께 정렬합니다.'),
    card('format-copy', '예시 서식 등록·적용 | 우리 기관의 모양으로',
         [line('예시 문서: □ 계획', size=35, bold=True), line('처리할 문서: {□ 안내}', size=23),
          line('크기·기호·여백이 다름', size=25)],
         [line('예시 문서: □ 계획', size=35, bold=True), line('처리할 문서: {□ 안내}', size=35, bold=True),
          line('같은 역할의 모양을 적용', size=25)],
         '빨간 대상 글자의 모양만 배웁니다. 예시 문서의 내용으로 바꾸거나 화면 전체를 복제하지 않습니다.'),
    card('format-manage', '서식 관리 | 이름과 값을 수정해 재사용',
         [line('등록된 서식'), line('{교육 계획 서식}'), line('□ 글자 크기: {16pt}')],
         [line('등록된 서식'), line('{[교육팀] 기본 서식}'), line('□ 글자 크기: {18pt}')],
         '사용자가 이름·기관·세부 값을 바꾼 예시입니다. 저장한 뒤 선택하여 적용합니다.'),
    card('table-convert', '텍스트 표 변환 | 박스 문자를 편집 가능한 표로',
         [line('{┌────┬────┐}'), line('{│ 항목  │ 인원  │}'),
          line('{├────┼────┤}'), line('  교육     20'), line('{└────┴────┘}')],
         [['{항목}', '{인원}'], ['교육', '20']],
         '빨간 박스 문자가 실제 표 테두리로 바뀝니다. 항목·인원은 머리글 모양이 적용되는 예시입니다.', 'table'),
    card('table-format', '표 서식 | 머리글과 본문을 역할별로',
         [['{항목}', '{인원}'], ['{교육}', '{20}'], ['{점검}', '{5}']],
         [['{항목}', '{인원}'], ['{교육}', '{20}'], ['{점검}', '{5}']],
         '빨간 글자의 크기·정렬·모양과 칸 배경을 바꿉니다. 제목·개요 등 서식 표는 별도로 처리합니다.', 'table'),
    card('table-width', '표 칸 너비 | 글이 긴 칸에 공간을 배분',
         [['항목', '세부 내용'], ['교육', '{주민 교육을}'], ['', '{운영합니다.}']],
         [['항목', '세부 내용'], ['교육', '{주민 교육을 운영합니다.}']],
         '빨간 글의 줄 배치가 바뀝니다. 열 너비를 글자 수와 최소 폭을 고려해 본문 폭 안에 맞춥니다.', 'width'),
    card('labels', '문두 라벨·괄호 | 강조와 크기를 구분',
         [line('ㅇ {(대상)} 주민 교육'), line('ㅇ 일정: {교육(오전)}')],
         [line('ㅇ {(대상)} 주민 교육', bold=True), line('ㅇ 일정: {교육(오전)}', size=26)],
         '라벨 강조·괄호 축소를 설명하는 도해입니다. 실제로는 대상 라벨·괄호 구간에만 설정을 적용합니다.'),
    card('spacing-rules', '공백·기호 정리 | 바뀌는 자리를 표시',
         [line('{ㅁ} 추진 계획'), line('교육{,}점검'), line('({·}대상{·}) 주민'), line('2026.{10.09.}')],
         [line('{□} 추진 계획'), line('교육{, }점검'), line('(대상) 주민'), line('2026.{ 10. 9.}')],
         '빨간 부분이 바뀝니다. 전 그림의 빨간 ·는 삭제할 공백을 보이게 한 표시이며 실제 글자가 아닙니다.'),
    card('asterisk', '별표 위첨자 | 본문 표시와 주석을 구분',
         [line('ㅇ 사전 신청자{*} 대상'), line('* 신청 방법 별도 안내')],
         [line('ㅇ 사전 신청자{*} 대상'), line('* 신청 방법 별도 안내')],
         '본문 단어 뒤의 빨간 별표만 위첨자로 바꿉니다. 줄 앞 주석 별표는 본문 표시와 구분합니다.', 'asterisk'),
    card('abbreviation', '준말·라벨 입력 | 등록된 표와 기호로 변환',
         [line('{제목1: 주민 교육 계획}'), line('{네모: 추진 계획}'), line('{원: 교육을 실시합니다.}')],
         [line('{주민 교육 계획}', size=35, bold=True), line('{□} 추진 계획'), line('{ㅇ} 교육을 실시합니다.')],
         '제목은 서식 표, 라벨은 문두기호로 바뀝니다. 준말 변환은 등록된 줄 앞 준말과 콜론이 대상입니다.'),
    card('options', '작업 옵션 | 고칠 범위를 선택',
         [line('본문: ㅇ 교육을 {실}'), line('{시합니다.}', 25), line('표 안: 안내를 {배}'), line('{포합니다.}', 25)],
         [line('본문: ㅇ 교육을 {실시합니다.}'), line('표 안: 안내를 배'), line('포합니다.', 25), line('예시 옵션: 표 제외 켬', size=25)],
         '표 제외를 켠 자간 정리의 예시입니다. 초기화·자간 포함·쪽 맞춤 옵션으로 범위를 선택합니다.'),
    card('reset-spacing', '기존 자간 초기화 | 0%를 출발점으로',
         [line('{ㅇ 주민 교육을 안내합니다.}', size=26), line('기존 자간: {-5%}', size=25)],
         [line('{ㅇ 주민 교육을 안내합니다.}', size=29), line('초기화 후 자간: {0%}', size=25),
          line('이어서 자간 정리를 실행', size=25)],
         '빨간 문장의 글자 사이 간격을 초기화합니다. 초기화를 꺼도 이후 자간 정리는 실행됩니다.'),
    card('range', '여러 문서·쪽 범위 | 지정한 대상만 실행',
         [line('1쪽: □ 안내'), line('2쪽: {ㅁ 추진 계획}'), line('3쪽: □ 붙임')],
         [line('1쪽: □ 안내'), line('2쪽: {□ 추진 계획}'), line('3쪽: □ 붙임')],
         '2쪽만 지정해 기호를 정리한 예시입니다. 쪽 범위 작업에서는 일부 구조 변환을 건너뜁니다.'),
    card('input', '텍스트 붙여넣기·정리 | 글을 처리 목록으로',
         [line('{##} 추진 계획'), line('{**}교육 안내{**}'), line('{개요:} 교육을 실시함')],
         [line('추진 계획'), line('교육 안내'), line('{교육을 실시함}'), line('새 문서를 목록에 추가', size=25)],
         'Markdown 표시를 정리하고 글을 새 문서로 추가하는 예시입니다. 정리·라벨 해석은 선택에 따릅니다.'),
    card('outliner', '아웃라이너 | 항목을 한 단계 안으로',
         [line('ㅁ 추진 계획'), line('{ㅁ 교육 운영}'), line('{ㅁ 사전 안내}')],
         [line('ㅁ 추진 계획'), line('{ㅇ 교육 운영}', 40), line('{- 사전 안내}', 80)],
         'Tab·Shift+Tab으로 계층을 바꿉니다. 빨간 항목의 기호와 들여쓰기 위치가 함께 바뀝니다.'),
    card('writing', '작성 도우미 | 금액·날짜·숫자를 정리',
         [line('금액: 1,250,000원'), line(''), line('날짜: 2026. 10. 9.'), line('인원: {20 + 5}'),
          line('목록: {교육, 점검}', size=25)],
         [line('금액: {금}1,250,000원'), line('{(금일백이십오만원)}', 75),
          line('날짜: 2026. 10. 9.{(금)}'), line('인원: {25}'), line('목록: {1. 교육 / 2. 점검}', size=25)],
         '사용자가 선택한 도구의 결과 예시입니다. 본문 전체의 금액·날짜·표를 자동 교체하는 기능은 아닙니다.'),
    card('review', '문서 구조·가독성 검토 | 고치기 전에 확인',
         [line('□ 추진 계획'), line('ㅇ 교육을 실시합니다.'), line('{□ 소요 예산}', size=23)],
         [line('□ 추진 계획'), line('ㅇ 교육을 실시합니다.'), line('□ 소요 예산', size=23),
          line('{검토 후보: □ 글자 크기 차이}', size=25)],
         '읽기 전용 검토는 원문을 바꾸지 않습니다. 빨간 글은 새로 표시되는 검토 결과입니다.'),
    card('proofread', '공공언어·맞춤법 검토 | 승인한 후보만 교정',
         [line('{금번} 교육을 안내합니다.'), line('담당 부서에 문의하세요.')],
         [line('{이번} 교육을 안내합니다.'), line('담당 부서에 문의하세요.'), line('승인한 교정을 새 파일로 저장', size=25)],
         '빨간 단어만 교체한 예시입니다. 내장 규칙의 후보를 확인하고 승인하여 적용합니다.'),
    card('markdown', 'Markdown 내보내기 | 본문과 표를 텍스트로',
         [line('교육 안내', size=35, bold=True), line('교육을 실시합니다.'), line('표: 항목 / 인원')],
         [line('{## }교육 안내'), line('교육을 실시합니다.'), line('{| }항목{ | }인원{ |}'),
          line('{| --- | --- |}')],
         '빨간 글은 출력 형식에 필요한 표시입니다. 원본 문서는 바꾸지 않고 새 Markdown 파일을 만듭니다.'),
    card('convert', '지원 파일 변환 | 작업용 HWPX로 읽기',
         [line('원본: 업무안내{.docx}'), line('교육을 실시합니다.'), line('편집 전 변환이 필요한 파일')],
         [line('작업용: 업무안내{.hwpx}'), line('교육을 실시합니다.'), line('한/글에서 후처리 가능')],
         'DOC·DOCX·PDF 등은 선택형 엔진이 필요합니다. 변환 후 구조·글꼴·OCR 결과를 확인합니다.'),
    card('results', '새 결과 파일·검수 | 원본 보존과 확인',
         [line('원본: 업무보고.hwp'), line('원본 폴더에 문서 1개')],
         [line('원본: 업무보고.hwp'), line('결과: {업무보고(일괄적용).hwpx}', size=24),
          line('{최종 점수·확인할 문제 표시}', size=25)],
         '원본은 그대로 두고 새 결과와 검사 정보를 만듭니다. 검수 보고서 파일 생성은 설정에 따릅니다.'),
    card('update', '업데이트·설정 보관 | Beta 13 시작 확인',
         [line('실행 중: {이전 베타}'), line('설정: 기존 사용자 설정'), line('서식: 등록한 기관 서식')],
         [line('실행 중: {1.72 Beta 13}'), line('설정: 기존 사용자 설정'), line('서식: 등록한 기관 서식')],
         'Beta 13부터 업데이트 후 새 앱 시작을 확인합니다. 설정·서식은 앱 데이터 폴더에 따로 보관합니다.'),
    card('original-layout', '서식 통일의 원본 쪽 구성 유지 | 쪽 수를 기준으로',
         [line('원본: 3쪽'), line('□ 추진 계획'), line('ㅇ {자료를 배포합니다.}', size=23),
          line('다른 글자 크기: 12pt', size=25)],
         [line('결과 목표: 3쪽'), line('□ 추진 계획'), line('ㅇ {자료를 배포합니다.}'),
          line('서식 교정 후 쪽 구성을 맞춤', size=25)],
         'HWP·HWPX 원본의 보고서별 쪽 구성을 기준으로 보정합니다. 달성 여부는 결과 검수에서 확인합니다.'),
]


def table(draw, x, y, rows, widths, header=False, size=23):
    row_height = 68
    for i, row in enumerate(rows):
        offset = 0
        for j, value in enumerate(row):
            w = widths[j]
            draw.rectangle((x + offset, y + i * row_height, x + offset + w, y + (i + 1) * row_height),
                           fill='#e9eff8' if header and i == 0 else 'white', outline='#8293a8', width=2)
            end = rich(draw, x + offset + 12, y + i * row_height + 17, value, size, header and i == 0)
            if end > x + offset + w - 4:
                raise ValueError(f'표 글자가 칸을 넘습니다: {value}')
            offset += w


def pages(draw, x, kind, after):
    top, w, h = 211, 266, 365
    for index in range(2):
        px = x + index * 295
        draw.rounded_rectangle((px, top, px + w, top + h), radius=8, fill='white', outline='#a8b5c5', width=2)
        draw.text((px + 16, top + h - 40), f'{index + 1}쪽' + (' (비워짐)' if kind == 'page-fit' and after and index == 1 else ''),
                  font=font(20), fill=GRAY)
    if kind == 'page-fit':
        for i in range(5):
            rich(draw, x + 16, top + 23 + i * (48 if after else 60), 'ㅇ 앞쪽 본문', 24)
        px = x + 16 if after else x + 311
        py = top + 280 if after else top + 23
        rich(draw, px, py, '{마지막 안내 문장}', 24)
    else:
        for i in range(3):
            rich(draw, x + 16, top + 23 + i * 60, 'ㅇ 앞쪽 본문', 24)
        rich(draw, x + (311 if after else 16), top + (23 if after else 270), '{□ 추진 계획}', 25, True)
        rich(draw, x + 311, top + (100 if after else 23), '{ㅇ 교육 운영}', 24)
        rich(draw, x + 311, top + (155 if after else 78), '{- 사전 안내}', 24)
        table(draw, x + 311, top + (210 if after else 133), [['{항목}', '{인원}']], [118, 118])


def render(c):
    im = Image.new('RGB', (1440, 760), '#f3f6fa')
    d = ImageDraw.Draw(im)
    d.text((42, 25), c['title'], font=font(36, True), fill=INK)
    d.text((42, 85), '1.72 Beta 13 기능 설명용 예시 · 실제 처리 화면 아님', font=font(23), fill=GRAY)
    for after, px, label in [(False, 40, '전 | 실행 전'), (True, 752, '후 | 선택한 작업 실행 후')]:
        d.rounded_rectangle((px, 137, px + 648, 625), radius=16, fill='white', outline='#d5deea', width=2)
        d.rounded_rectangle((px, 137, px + 648, 189), radius=16, fill='#e7edf5')
        d.text((px + 23, 145), label, font=font(26, True), fill=INK)
        entries = c['after' if after else 'before']
        if c['kind'].startswith('page-'):
            pages(d, px + 28, c['kind'], after)
        elif c['kind'] in ('table', 'width') and (after or c['name'] != 'table-convert'):
            widths = ([120, 456] if after else [288, 288]) if c['kind'] == 'width' else [288, 288]
            table(d, px + 32, 240, entries, widths, after,
                  19 if c['name'] == 'table-format' and not after else 23)
        elif c['kind'] == 'asterisk' and after:
            end = rich(d, px + 32, 232, 'ㅇ 사전 신청자', 29)
            end = rich(d, end, 222, '{*}', 24)
            rich(d, end, 232, ' 대상', 29)
            rich(d, px + 32, 304, '* 신청 방법 별도 안내', 29)
        elif c['name'] == 'labels':
            end = rich(d, px + 32, 225, 'ㅇ ', 29)
            end = rich(d, end, 225, '{(대상)}', 29, after)
            rich(d, end, 225, ' 주민 교육', 29)
            end = rich(d, px + 32, 295, 'ㅇ 일정: 교육', 29)
            rich(d, end, 298 if after else 295, '{(오전)}', 25 if after else 29)
        elif c['name'] == 'reset-spacing':
            xpos = px + 32
            for char in 'ㅇ 주민 교육을 안내합니다.':
                rich(d, xpos, 225, '{' + char + '}', 29)
                xpos += d.textlength(char, font=font(29)) * (0.95 if not after else 1)
            for i, entry in enumerate(entries[1:], 1):
                rich(d, px + 32, 225 + i * 70, entry['text'], entry['size'])
        else:
            for i, entry in enumerate(entries):
                offset = d.textlength('ㅇ (대상) ', font=font(29)) if c['name'] == 'hanging-indent' and after and i > 0 else entry['x']
                end = rich(d, px + 32 + offset, 225 + i * 70, entry['text'], entry['size'], entry['bold'])
                if end > px + 620:
                    raise ValueError(f"패널 밖 텍스트: {c['name']}: {entry['text']}")
            if c['name'] == 'hanging-indent' and after:
                # 첫 줄 본문 시작과 이어지는 줄 시작을 함께 표시.
                guide = px + 32 + d.textlength('ㅇ (대상) ', font=font(29))
                for y in range(216, 430, 14):
                    d.line((guide, y, guide, y + 7), fill=RED, width=2)
        if c['name'] in ('all-in-one', 'abbreviation') and after:
            d.rectangle((px + 18, 215, px + 622, 284), outline=RED, width=2)
    d.text((42, 650), '빨간색 = 변경되는 글자·서식·위치 또는 새로 표시되는 결과', font=font(25, True), fill=RED)
    # 안내 문구는 긴 경우 두 줄로 나눠 그림 안에 모두 담는다.
    words = c['note'].split()
    lines, current = [], ''
    for word in words:
        trial = (current + ' ' + word).strip()
        if d.textlength(trial, font=font(22)) > 1350:
            lines.append(current)
            current = word
        else:
            current = trial
    lines.append(current)
    for i, value in enumerate(lines):
        d.text((42, 695 + i * 27), value, font=font(22), fill=GRAY)
    if len(lines) > 2:
        raise ValueError('설명 문구가 너무 깁니다.')
    im.save(OUT / f"{c['name']}.png", optimize=True)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    generated = 0
    for comparison in CARDS:
        if comparison['name'] in ('spacing', 'all-in-one') and (OUT / 'test4-evidence.json').is_file():
            if not (OUT / (comparison['name'] + '.png')).is_file():
                raise RuntimeError('실제 사례 이미지는 build_test4_comparisons.py로 재생성하세요.')
            continue
        render(comparison)
        generated += 1
    print(f'{generated}개 설명용 전후 비교 이미지 생성: {OUT}')
