"""HWIRE2: 위계 엔진 결과가 쪽 맞춤 묶음 수집에 반영되는지(켬/끔 비교). 한/글 COM은 쓰지 않는다."""
import unittest
from unittest.mock import patch

from docfit_app import hierarchy_bridge as hb
from docfit_engine.page_fit import _install

LINES = [' ㅇ 부모 문장', '  기호 없는 이어진 문장', ' ㅇ 다음 항목']


class Doc:
    pos = (0, 0, 0)

    def GetPos(self):
        return self.pos

    def SetPos(self, *pos):
        self.pos = pos

    def run(self, action):
        area, i, offset = self.pos
        if action == 'MoveParaBegin':
            offset = 0
        elif action == 'MoveParaEnd':
            offset = len(LINES[i])
        elif action == 'MoveNextParaBegin':
            i, offset = min(i + 1, len(LINES) - 1), 0
        self.pos = area, i, offset


class WireTest(unittest.TestCase):
    def collect(self, settings, engine_result):
        doc = Doc()
        calls = []

        def fake(paragraphs, settings=None, executable=None, timeout=5.0):
            calls.append(paragraphs)
            if not (settings or {}).get('hierarchy_engine', False):
                return None
            return engine_result

        ns = {'hwp': doc, 'hwp_run': doc.run, '위계엔진_설정': settings,
              '현재문단_텍스트': lambda: LINES[doc.pos[1]], '중단_요청됨': lambda: False,
              '보고서_문단역할': lambda t: '본문' if t.lstrip().startswith('ㅇ') else None,
              '세트문장_선행들여쓰기_폭': lambda t: len(t) - len(t.lstrip()),
              '세트문장_후속문단인가': lambda indent, t: True,
              '쪽맞춤_부연설명인가': lambda t: False}
        ns['엔진_문단역할_보조'] = _install(_docfit_namespace=ns, _docfit_symbol='엔진_문단역할_보조')
        fn = _install(_docfit_namespace=ns, _docfit_symbol='보고서_본문묶음_수집')
        with patch.object(hb, 'analyze_levels', fake):
            return fn((0, 0, 0)), calls

    def test_off_equals_engine_none(self):
        off, calls_off = self.collect({}, {"levels": [5, 5], "confidence": 9})
        none, _ = self.collect({'hierarchy_engine': True}, None)
        self.assertEqual(off, none)
        self.assertEqual(calls_off, [])  # 꺼짐이면 엔진 호출 자체가 없다

    def test_on_engine_agrees_with_fallback_role(self):
        base, _ = self.collect({}, None)
        on, calls = self.collect({'hierarchy_engine': True}, {"levels": [5, 7], "confidence": 9})
        self.assertEqual([r for _, _, r in base], ['본문', '부연설명'])
        self.assertEqual([r for _, _, r in on], ['본문', '부연설명'])
        self.assertTrue(calls)

    def test_on_engine_role_used_when_base_unknown(self):
        # 엔진이 '본문'으로 판정하면 기존의 부연설명 대체 판정 대신 그 역할이 기록된다.
        on, _ = self.collect({'hierarchy_engine': True}, {"levels": [5, 5], "confidence": 9})
        self.assertEqual([r for _, _, r in on], ['본문', '본문'])

    def test_engine_hold_keeps_existing_rule(self):
        base, _ = self.collect({}, None)
        hold, _ = self.collect({'hierarchy_engine': True}, {"levels": [5, 10], "confidence": 1})
        self.assertEqual(base, hold)

    def test_role_mapping(self):
        with patch.object(hb, 'analyze_levels', lambda *a, **k: {"levels": [4, 5, 6, 7]}):
            self.assertEqual(hb.engine_role_of_last([{}] * 4, {"hierarchy_engine": True}), '부연설명')
        with patch.object(hb, 'analyze_levels', lambda *a, **k: {"levels": [1]}):
            self.assertIsNone(hb.engine_role_of_last([{}], {"hierarchy_engine": True}))


if __name__ == '__main__':
    unittest.main()
