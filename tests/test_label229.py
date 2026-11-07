"""LABEL229: '라벨: ①' 다음 문단 '②'의 글자 모양을 ①과 같게 — 실제 표준서식 XML 경로 연결 시험."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from docfit_core.batch_format import plain_text, tag
from tests.test_batch_format import roots

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / 'fixtures/c23_continuation.hwpx'


def describe(path):
    """문단마다 (글, (left, intent), [(글꼴, 크기, 굵게, 글)])."""
    header, root = roots(path)
    chars = {c.get('id'): c for c in header.iter() if tag(c) == 'charPr'}
    paras = {c.get('id'): c for c in header.iter() if tag(c) == 'paraPr'}
    fonts = {f.get('id'): f.get('face') for ff in header.iter()
             if tag(ff) == 'fontface' and ff.get('lang') == 'HANGUL' for f in ff if tag(f) == 'font'}
    result = []
    for p in root:
        if tag(p) != 'p':
            continue
        shape = paras[p.get('paraPrIDRef')]
        geo = tuple(int(next(x for x in shape.iter() if tag(x) == k).get('value')) for k in ('left', 'intent'))
        runs = []
        for run in p:
            if tag(run) != 'run':
                continue
            c = chars[run.get('charPrIDRef')]
            ref = next(x for x in c if tag(x) == 'fontRef')
            runs.append((fonts.get(ref.get('hangul')), c.get('height'),
                         any(tag(x) == 'bold' for x in c), run[0].text or ''))
        result.append((plain_text(p), geo, runs))
    return result


def shape_at(runs, index):
    """글 위치 index의 글자 모양(글꼴, 크기, 굵게)."""
    for face, height, bold, text in runs:
        if index < len(text):
            return face, height, bold
        index -= len(text)
    raise IndexError(index)


class Label229ContinuationWiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = staticmethod(runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))['표준서식_hwpx_처리'])

    def run_formatter(self, folder, name, **overrides):
        logs = []
        values = {'알파_일괄서식_가능': lambda: True, '표준서식_내어쓰기_사용': True,
                  '_알파_글꼴형식': lambda face: 'TTF', '로그': logs.append,
                  '활성_서식예시_파일': None}
        values.update(overrides)
        output = Path(folder) / name
        with patch.dict(self.fn.__globals__, values):
            self.assertGreater(self.fn(FIXTURE, output), 0)
            xml_texts = set(self.fn.__globals__['_표준서식_XML텍스트'])
        return describe(output), logs, xml_texts

    def baseline(self, folder):
        """연결 전 동작: 연속 줄 맞춤을 부르지 않은 결과."""
        with patch('docfit_core.continuation.align_hwpx_in_place', lambda *a, **k: set()):
            return self.run_formatter(folder, 'before.hwpx')[0]

    def test_second_item_takes_first_item_char_shape_and_others_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            before = self.baseline(folder)
            after, logs, xml_texts = self.run_formatter(folder, 'after.hwpx')
        p_text, p_geo, p_runs = after[0]
        body = p_text.index('①')
        expected = shape_at(p_runs, body)          # ① 본문 글자 모양
        # 연결 전에는 ②·③이 다른 글자 모양(다른 기호 규칙)을 받았다 — 시험이 실제 차이를 재는지 확인.
        self.assertNotEqual(shape_at(before[1][2], before[1][0].index('②')), expected)
        for index, marker in ((1, '②'), (2, '③')):
            text, geo, runs = after[index]
            with self.subTest(marker=marker):
                self.assertTrue(text.startswith(marker))                  # 앞 빈칸은 여백으로 대체
                self.assertEqual(text.strip(), before[index][0].strip())  # 글자 보존
                self.assertEqual({shape_at(runs, i) for i in range(len(text))}, {expected})
                self.assertEqual(geo[0], p_geo[0])                         # 둘째 줄 = ① 줄 둘째 줄
                self.assertLess(geo[1], 0)
                self.assertIn(text, xml_texts)                             # 뒤 COM 표준서식이 글꼴을 덮지 않음
        # ①줄: 글자 모양은 그대로, 둘째 줄이 '① ' 뒤 본문에 맞도록 내어쓰기만 바뀐다.
        self.assertEqual(after[0][2], before[0][2])
        self.assertEqual(p_geo, (p_geo[0], -p_geo[0]))
        self.assertGreater(p_geo[0], 0)
        # ②의 첫 줄(left + intent)은 ① 위치 = ①줄 둘째 줄 위치 - 폭('① ')보다 앞이다.
        self.assertLess(after[1][1][0] + after[1][1][1], p_geo[0])
        self.assertGreater(after[1][1][0] + after[1][1][1], 0)
        # 다른 문단(한 줄에 ①②가 함께 있는 문단, 빈 문단)은 그대로.
        self.assertEqual(after[3:], before[3:])
        self.assertTrue(any('[연속 줄 맞춤]' in str(m) for m in logs))

    def test_disabled_hanging_indent_or_profile_rule_leaves_result_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('docfit_core.continuation.align_hwpx_in_place', lambda *a, **k: set()):
                off_before = self.run_formatter(folder, 'off0.hwpx', 표준서식_내어쓰기_사용=False)[0]
            off_after = self.run_formatter(folder, 'off1.hwpx', 표준서식_내어쓰기_사용=False)[0]
            self.assertEqual(off_after, off_before)
            settings = dict(self.fn.__globals__.get('표준서식_설정') or {})
            for rule in ('none', 'fixed', 'after_marker'):
                with self.subTest(rule=rule):
                    profile = dict(settings, 내어쓰기_규칙={'•': rule})
                    with patch('docfit_core.continuation.align_hwpx_in_place', lambda *a, **k: set()):
                        before = self.run_formatter(folder, f'{rule}0.hwpx', 표준서식_설정=profile)[0]
                    after = self.run_formatter(folder, f'{rule}1.hwpx', 표준서식_설정=profile)[0]
                    self.assertEqual(after, before)

    def test_failure_keeps_batch_result(self):
        def boom(*args, **kwargs):
            raise RuntimeError('측정 실패')
        with tempfile.TemporaryDirectory() as folder:
            before = self.baseline(folder)
            with patch('docfit_core.continuation.align_hwpx_in_place', boom):
                after, logs, _ = self.run_formatter(folder, 'fail.hwpx')
            self.assertEqual(after, before)
            self.assertTrue(any('[연속 줄 맞춤] 건너뜀' in str(m) for m in logs))
            self.assertFalse(any(p.name.endswith('.tmp') for p in Path(folder).iterdir()))

    def test_in_place_is_idempotent(self):
        from docfit_core.continuation import align_hwpx_in_place
        with tempfile.TemporaryDirectory() as folder:
            after = self.run_formatter(folder, 'after.hwpx')[0]
            output = Path(folder) / 'after.hwpx'
            align_hwpx_in_place(output, original=FIXTURE)
            self.assertEqual(describe(output), after)
            self.assertEqual([p.name for p in Path(folder).iterdir() if p.name.endswith('.tmp')], [])


if __name__ == '__main__':
    unittest.main()
