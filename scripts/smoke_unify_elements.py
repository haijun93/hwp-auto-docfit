"""서식통일 고도화 실측: 생성 문서로 정렬·기울임·밑줄·왼쪽 여백 예외 문장만 고치는지 확인한다.

사용자 문서는 쓰지 않는다. 한/글 COM 인스턴스를 따로 띄우고 끝나면 닫는다(사용자 한/글 창과 무관).
결과는 reports/unify-elements/ 아래에 남는다.
"""
import json
from pathlib import Path
import runpy
import sys
import tempfile
from zipfile import ZipFile

from defusedxml import ElementTree as ET
import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docfit_core.format_elements import HeaderIndex, paragraph_values, _tag  # noqa: E402


def snapshot(path):
    """본문 문단별 (글자, 요소 값)."""
    with ZipFile(path) as archive:
        index = HeaderIndex(ET.fromstring(archive.read('Contents/header.xml')))
        section = ET.fromstring(archive.read('Contents/section0.xml'))
    result = []
    for p in (x for x in section if _tag(x) == 'p'):
        found = paragraph_values(p, index)
        if found:
            result.append((found[2], found[3]))
    return result


def main():
    folder = ROOT / 'reports' / 'unify-elements'
    folder.mkdir(parents=True, exist_ok=True)
    run_folder = Path(tempfile.mkdtemp(prefix='generated-', dir=folder))
    source, result = run_folder / 'input.hwpx', run_folder / 'result.hwpx'
    ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))
    fn = ns['서식통일_전체_적용']
    g = fn.__globals__
    pythoncom.CoInitialize()
    app = None
    try:
        app = win32com.client.DispatchEx('HwpFrame.HwpObject')
        app.RegisterModule(g['REGISTER_MODULE_NAME'], g['REGISTER_MODULE_VALUE'])
        g.update(hwp=app, 작업_모드='unify', 쪽범위_실제=None, 쪽범위_본문_문단=None,
                 _서식통일_문서대표프로필={}, 로그=lambda *_: None, 진단로그=lambda *_: None,
                 _서식통일_대표값_검토콜백=None)
        app.Run('FileNew')
        texts = [f'ㅇ 기준 문장 {i}번은 양쪽 정렬과 보통 글자로 씁니다' for i in range(1, 6)]
        texts += ['ㅇ 가운데 정렬 예외 문장입니다', 'ㅇ 기울임 예외 문장입니다',
                  'ㅇ 밑줄 예외 문장입니다', 'ㅇ 왼쪽 여백 예외 문장입니다']
        g['텍스트_삽입']('\r\n'.join(texts))
        for i, text in enumerate(texts):
            g['단어모드_범위선택']((0, i, 0), (0, i, len(text)))
            g['문자모양_적용_현재선택'](폰트='함초롬바탕', 크기_pt=15, 굵게=False, 자간=0)
            app.Run('Cancel')

        def char_set(i, **items):
            g['단어모드_범위선택']((0, i, 0), (0, i, len(texts[i])))
            action = app.CreateAction('CharShape')
            params = action.CreateSet()
            for key, value in items.items():
                params.SetItem(key, value)
            assert action.Execute(params) is not False
            app.Run('Cancel')

        def para_set(i, **items):
            app.SetPos(0, i, 0)
            action = app.CreateAction('ParagraphShape')
            params = action.CreateSet()
            for key, value in items.items():
                params.SetItem(key, value)
            assert action.Execute(params) is not False

        para_set(5, AlignType=3)
        char_set(6, Italic=1)
        char_set(7, UnderlineType=1)
        para_set(8, LeftMargin=2000)
        assert app.SaveAs(str(source), 'HWPX', '') is not False
        before = snapshot(source)
        assert before[5][1]['align'] == 'CENTER' and before[6][1]['italic'] and before[7][1]['underline'] == 'BOTTOM'
        assert before[8][1]['left'] == 1000, before[8][1]['left']
        assert fn() is True
        assert app.SaveAs(str(result), 'HWPX', '') is not False
        after = snapshot(result)
        checked = ('font', 'size', 'bold', 'italic', 'underline', 'align', 'left', 'right', 'color')
        for i in range(5):
            assert {k: before[i][1][k] for k in checked} == {k: after[i][1][k] for k in checked}, \
                f'기준 문장 {i} 변경됨'
        assert after[5][1]['align'] == 'JUSTIFY', after[5][1]['align']
        assert after[6][1]['italic'] is False, after[6][1]['italic']
        assert after[7][1]['underline'] == 'NONE', after[7][1]['underline']
        assert after[8][1]['left'] == 0, after[8][1]['left']
        for i in range(5, 9):
            assert after[i][0] == before[i][0], '글자가 바뀜'
        assert app.Open(str(result), 'HWPX', 'forceopen:true') is not False
        audit = fn(고정_프로필_재적용=True, 검증만=True)
        assert audit['status'] == 'passed', audit
        report = {'passed': True, 'source': str(source), 'result': str(result),
                  'normal_paragraphs_unchanged': 5,
                  'corrected': {'align': 'CENTER→JUSTIFY', 'italic': 'True→False',
                                'underline': 'BOTTOM→NONE', 'left': '1000→0'},
                  'audit': {k: audit[k] for k in ('status', 'checked')}}
        print(json.dumps(report, ensure_ascii=False))
    finally:
        if app is not None:
            try:
                app.Clear(1)
            finally:
                app.Quit()
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    main()
