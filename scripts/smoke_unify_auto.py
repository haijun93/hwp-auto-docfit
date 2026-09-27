"""Real COM smoke test using a generated document, never user documents."""
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
from docfit_core.style_inventory import _parse_char, _parse_fonts, _run_text, _tag


def snapshot(path):
    with ZipFile(path) as archive:
        header = ET.fromstring(archive.read('Contents/header.xml'))
        fonts = _parse_fonts(header)
        chars = {e.get('id'): e for e in header.iter() if _tag(e) == 'charPr'}
        section = ET.fromstring(archive.read('Contents/section0.xml'))
        paragraphs = []
        for para in section:
            if _tag(para) != 'p':
                continue
            values = []
            for run in para:
                if _tag(run) != 'run':
                    continue
                char = chars[run.get('charPrIDRef')]
                parsed = _parse_char(char, fonts)
                spacing = next((tuple(sorted(e.attrib.items())) for e in char if _tag(e) == 'spacing'), ())
                for letter in _run_text(run):
                    values.append((letter, parsed['font'], parsed['size_pt'], parsed['bold'], spacing, parsed['color']))
            paragraphs.append(values)
        return paragraphs


def main():
    folder = ROOT / 'reports' / 'unify-auto'
    folder.mkdir(parents=True, exist_ok=True)
    run_folder = Path(tempfile.mkdtemp(prefix='generated-', dir=folder))
    source, result = run_folder / 'input.hwpx', run_folder / 'result.hwpx'
    ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))
    fn = ns['서식통일_전체_적용']
    globals_ = fn.__globals__
    pythoncom.CoInitialize()
    app = None
    try:
        # No fallback to an existing user's COM session.
        app = win32com.client.DispatchEx('HwpFrame.HwpObject')
        app.RegisterModule(globals_['REGISTER_MODULE_NAME'], globals_['REGISTER_MODULE_VALUE'])
        globals_.update(hwp=app, 쪽범위_실제=None, 쪽범위_본문_문단=None,
                        _서식통일_문서대표프로필={}, 로그=lambda *_: None, 진단로그=lambda *_: None)
        app.Run('FileNew')
        texts = ['ㅇ 정상 문단 하나', 'ㅇ 정상 문단 둘', 'ㅇ 정상 문단 셋',
                 'ㅇ 크기 예외 문단 ' + '행정서비스를 제공하기 위한 구체적인 운영방안을 검토합니다. ' * 9,
                 '※ 미확정 문단 하나', '※ 미확정 문단 둘']
        sizes = [15, 15, 15, 17, 12, 14]
        globals_['텍스트_삽입']('검증용 문서')
        app.Run('BreakPara')
        globals_['텍스트_삽입']('\r\n'.join(texts))
        for i, (text, size) in enumerate(zip(texts, sizes), start=1):
            globals_['단어모드_범위선택']((0, i, 0), (0, i, len(text)))
            globals_['문자모양_적용_현재선택'](폰트='함초롬바탕', 크기_pt=size, 굵게=False, 자간=0)
            app.Run('Cancel')
        # Intentionally mixed word spacing inside the unresolved paragraph.
        for start, end, spacing in [(2, 5, -5), (6, 8, -10)]:
            globals_['단어모드_범위선택']((0, 5, start), (0, 5, end))
            globals_['문자모양_적용_현재선택'](자간=spacing)
            app.Run('Cancel')
        assert app.SaveAs(str(source), 'HWPX', '') is not False
        before = snapshot(source)[1:]
        assert all(v[2] == 15 for para in before[:3] for v in para), 'Fixture setup failed'
        calls = []
        def review(kind, payload):
            calls.append(kind)
            assert kind == 'profile', 'Unexpected per-paragraph approval dialog'
            return {'approved': True}
        globals_['_서식통일_대표값_검토콜백'] = review
        assert fn() is True
        assert app.SaveAs(str(result), 'HWPX', '') is not False
        after = snapshot(result)[1:]
        assert calls == ['profile'], calls
        assert before[:3] == after[:3], 'Normal paragraphs changed'
        assert all(value[2] == 15 for value in after[3]), 'Outlier was not corrected'
        assert all(-10 <= int(value) <= 10 for char in after[3] for _, value in char[4]), 'Unsafe spacing'
        for index in (4, 5):
            assert [value[:-1] for value in before[index]] == [value[:-1] for value in after[index]], 'Red marking changed non-color properties'
            assert all(value[-1].upper() == '#FF0000' for value in after[index]), 'Missing red marking'
        assert app.Open(str(result), 'HWPX', 'forceopen:true') is not False
        audit = fn(고정_프로필_재적용=True, 검증만=True)
        assert audit['status'] == 'incomplete', audit
        assert len(audit['unresolved']) == 2, audit
        assert not audit['issues'], audit
        report = {'passed': True, 'source': str(source), 'result': str(result),
                  'normal_paragraphs_unchanged': 3, 'outlier_corrected': 1,
                  'red_paragraphs': 2, 'mixed_spacing_preserved': True, 'audit': audit}
        print(json.dumps(report, ensure_ascii=True))
    finally:
        if app is not None:
            try:
                app.Clear(1)
            finally:
                app.Quit()
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    main()
