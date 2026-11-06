"""HWIRE3: 위계 엔진 결과가 서식통일 그룹키(문단 수준 판정)에 반영되는지 켬/끔 비교. 한/글 COM은 쓰지 않는다."""
import unittest
from collections import defaultdict
from unittest.mock import patch

from docfit_app import hierarchy_bridge as hb
from docfit_engine import formatter_unify
from docfit_engine.runtime import _plain_bind

# 서식통일_항목기호 가짜(실제는 unify_marker): ①은 역할을 기호만으로 못 정해 '원문자'로 남고(실제 동작),
# ◆는 역할이 비어 '미분류'가 된다. ㅇ은 기존 규칙이 '본문'.
MARKERS = {'◆': ('◆', '', '◆'), '①': ('①', '원문자', '①'), 'ㅇ': ('ㅇ', '본문', 'ㅇ')}


def _marker(text):
    return MARKERS.get(text.lstrip()[:1], ('', '', ''))


def make(name):
    ns = {'서식통일_항목기호': _marker, '항목기호_역할표': lambda: {}, '보고서_문단역할': lambda t: None,
          '진단로그': lambda *a, **k: None, '_서식통일_현재_HWPX': lambda: None,
          '서식통일_붙임제목': lambda t: '', '서식통일_체계전환점': lambda seq: [], 'defaultdict': defaultdict}
    fn = formatter_unify._install(_docfit_namespace=ns, _docfit_symbol=name, bind_function=_plain_bind)
    ns[name] = fn
    return fn, ns


class GroupKeyTest(unittest.TestCase):
    def setUp(self):
        self.key, _ = make('_서식통일_그룹키')

    def test_off_same_as_before(self):
        # 엔진 인자를 안 주면(꺼짐·실패) 기존과 같은 결과.
        self.assertEqual(self.key('◆', '◆ 항목', (0, 3, 0)), ('◆', '미분류', '문서 공통'))
        self.assertEqual(self.key('◆', '◆ 항목', (0, 3, 0), {}), ('◆', '미분류', '문서 공통'))
        self.assertEqual(self.key('', '◆ 항목', None, {3: '소제목'}), ('◆', '미분류', '문서 공통'))

    def test_on_engine_fills_only_unclassified(self):
        self.assertEqual(self.key('◆', '◆ 항목', (0, 3, 0), {3: '소제목'}), ('◆', '소제목', '문서 공통'))
        # 엔진이 이 문단을 판정하지 않으면(보류) 기존대로.
        self.assertEqual(self.key('◆', '◆ 항목', (0, 3, 0), {4: '소제목'}), ('◆', '미분류', '문서 공통'))

    def test_circled_marker_role_refined_by_engine(self):
        self.assertEqual(self.key('①', '① 항목', (0, 3, 0)), ('①', '원문자', '문서 공통'))
        self.assertEqual(self.key('①', '① 항목', (0, 3, 0), {3: '내용'}), ('①', '내용', '문서 공통'))

    def test_existing_rule_wins_over_engine(self):
        self.assertEqual(self.key('ㅇ', 'ㅇ 항목', (0, 3, 0), {3: '소제목'}), ('ㅇ', '본문', '문서 공통'))


class BridgeRolesTest(unittest.TestCase):
    ITEMS = [(0, '◆ 가'), (1, '  ㅇ 나'), (2, '    - 다')]

    def test_off_and_failure_are_empty(self):
        self.assertEqual(hb.engine_roles(self.ITEMS, {}), {})
        self.assertEqual(hb.engine_roles(self.ITEMS, {'hierarchy_engine': True}, executable='/nonexistent/x'), {})
        self.assertEqual(hb.engine_roles([], {'hierarchy_engine': True}), {})

    def test_on_maps_roles_and_skips_hold(self):
        seen = []

        def fake(paragraphs, settings=None, executable=None, timeout=5.0):
            seen.append(paragraphs)
            return {"levels": [4, 5, 10]}

        with patch.object(hb, 'analyze_levels', fake):
            roles = hb.engine_roles(self.ITEMS, {'hierarchy_engine': True})
        self.assertEqual(roles, {0: '소제목', 1: '본문'})  # 10(모호)은 판정 보류
        self.assertEqual([p['indent'] for p in seen[0]], [0, 2, 4])
        self.assertEqual(len(seen), 1)  # 엔진 호출은 한 번


class BoundaryTest(unittest.TestCase):
    def test_boundary_uses_engine_roles_only_when_given(self):
        fn, ns = make('_서식통일_체계경계')
        ns['_서식통일_그룹키'] = make('_서식통일_그룹키')[0]
        captured = []
        ns['서식통일_체계전환점'] = lambda seq: captured.append(dict(seq)) or []
        shape = (None, None)
        표본 = {'◆': [(shape, (0, 7, 0), (0, 7, 3), '◆ 항목')]}
        fn(표본, {})
        fn(표본, {}, {7: '소제목'})
        self.assertEqual([list(c) for c in captured],
                         [[('◆', '미분류')], [('◆', '소제목')]])


if __name__ == '__main__':
    unittest.main()
