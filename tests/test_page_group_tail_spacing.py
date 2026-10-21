"""Same-page paragraphs following a compressed group inherit its Percent spacing."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from docfit_engine.page_fit import _install


class TailSpacingTest(unittest.TestCase):
    def run_helper(self, counts=None, area_change=False, fail=False, cancel=False):
        # Group mode is 140 (not the preceding paragraph's 120 or first 150).
        values = {0: [0, 120], 1: [0, 150], 2: [0, 140], 3: [0, 140],
                  4: [0, 160], 5: [1, 180], 6: [0, 130], 7: [0, 140],
                  8: [0, 170], 9: [0, 180], 10: [0, 160], 11: [0, 190]}
        original = {p: list(v) for p, v in values.items()}
        doc = Mock()
        position = [0, 0, 9]
        doc.GetPos.side_effect = lambda: tuple(position)
        doc.SetPos.side_effect = lambda *pos: position.__setitem__(slice(None), pos)
        doc.LineSpacingMethod.return_value = 0
        shape = SimpleNamespace(HSet=object())
        doc.HParameterSet.HParaShape = shape

        def read(*args):
            shape.LineSpacingType, shape.LineSpacing = values[position[1]]

        doc.HAction.GetDefault.side_effect = read
        writes = []

        def action(*args):
            fields = {}
            pset = Mock()
            pset.SetItem.side_effect = fields.__setitem__
            act = Mock()
            act.CreateSet.return_value = pset

            def execute(_):
                p = position[1]
                writes.append((p, fields['LineSpacing']))
                values[p] = [fields['LineSpacingType'], fields['LineSpacing']]
                if fail and fields['LineSpacing'] == 140:
                    return False
                return True

            act.Execute.side_effect = execute
            return act

        doc.CreateAction.side_effect = action

        def move(cmd):
            self.assertEqual(cmd, 'MoveNextParaBegin')
            position[1] += 1
            position[2] = 0
            if area_change and position[1] == 10:
                position[0] = 1

        log = Mock()
        check = Mock(return_value={2: 3} if counts is None else counts)
        ns = {'hwp': doc, 'hwp_run': move, '중단_요청됨': lambda: cancel and bool(writes),
              '본문_컨트롤_문단번호': lambda: {8, 9},
              '문단_첫줄_쪽': lambda pos: 2 if pos[1] <= 10 else 3,
              '보고서_묶음_쪽별줄수': check, '진단로그': log}
        helper = _install(_docfit_namespace=ns, _docfit_symbol='_묶음뒤_같은쪽_줄간격_맞춤')
        group = [((0, p, 0), (0, p, 12), '본문') for p in (1, 2, 3)]
        if fail:
            with self.assertRaisesRegex(RuntimeError, '줄간격 적용 실패'):
                helper(group, 2)
            result = 0
        else:
            result = helper(group, 2)
        self.assertEqual(doc.GetPos(), (0, 0, 9))
        return result, values, original, writes, log, check

    def test_only_larger_percent_on_same_page_after_group(self):
        result, values, original, writes, log, check = self.run_helper()
        self.assertEqual(result, 2)
        self.assertEqual(writes, [(4, 140), (10, 140)])
        for p in set(values) - {4, 10}:
            self.assertEqual(values[p], original[p])
        check.assert_called_once()
        log.assert_called_once_with('[문장 묶음] 같은 쪽 묶음 뒤 2문단 줄간격 140%로 맞춤')

    def test_reverts_only_tail_if_group_leaves_target_page(self):
        for counts in ({2: 2, 3: 1}, {3: 3}, {}):
            with self.subTest(counts=counts):
                result, values, original, writes, log, _ = self.run_helper(counts=counts)
                self.assertEqual(result, 0)
                self.assertEqual(values, original)
                self.assertEqual(writes, [(4, 140), (10, 140), (4, 160), (10, 160)])
                log.assert_not_called()

    def test_stops_at_another_text_area(self):
        result, _, _, writes, _, _ = self.run_helper(area_change=True)
        self.assertEqual(result, 1)
        self.assertEqual(writes, [(4, 140)])

    def test_failed_action_restores_tail(self):
        _, values, original, _, log, _ = self.run_helper(fail=True)
        self.assertEqual(values, original)
        log.assert_not_called()

    def test_cancel_restores_tail(self):
        result, values, original, _, log, _ = self.run_helper(cancel=True)
        self.assertEqual(result, 0)
        self.assertEqual(values, original)
        log.assert_not_called()
