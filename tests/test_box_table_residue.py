"""선 문자 표 → 한/글 표 변환: 원래 줄이 지워지지 않았으면 다시 지우고, 끝내 못 지우면 표를 넣지 않는다(2026-10-11)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

BOX = ['  ┌──┬──┐', '  │ 가 │ 나 │', '  └──┴──┘']


class FakeHwp:
    """본문 문단 목록만 흉내 낸다. first_delete_fails면 첫 범위 지우기가 헛돈다(실측 재현)."""

    def __init__(self, paras, first_delete_fails=False, never_delete=False):
        self.paras = list(paras)
        self.pos = (0, 0, 0)
        self.sel = None
        self.fail_once = first_delete_fails
        self.never = never_delete

    def SetPos(self, a, p, c):
        self.pos = (a, min(p, len(self.paras) - 1), c)

    def GetPos(self):
        return self.pos

    def SelectText(self, sp, spos, ep, epos):
        self.sel = (sp, ep, epos)
        return True

    def run(self, name):
        if name == 'MoveParaEnd':
            self.pos = (0, self.pos[1], len(self.paras[self.pos[1]]))
        elif name == 'Delete' and self.sel:
            sp, ep, epos = self.sel
            self.sel = None
            if self.never or self.fail_once:
                self.fail_once = False
                return True                 # 한/글이 실패를 알리지 않고 헛도는 경우
            if epos == 0 and ep > sp:       # 다음 문단 시작까지: 문단째 지움
                del self.paras[sp:ep]
            else:
                self.paras[sp:ep + 1] = ['']
        return True


class BoxResidueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def run_replace(self, fake):
        fn = self.ns['_박스그림표_교체']
        inserted = []
        with patch.dict(fn.__globals__, {'hwp': fake, 'hwp_run': fake.run, '로그': Mock(),
                                         '현재문단_텍스트': lambda: fake.paras[fake.pos[1]],
                                         '_박스그림표_한글표_삽입': lambda rows: inserted.append(rows)}):
            try:
                fn(1, 3, [['가', '나']])
                return inserted, None
            except RuntimeError as e:
                return inserted, e

    def test_normal_delete_then_table(self):
        fake = FakeHwp(['앞 문단'] + BOX + ['뒤 문단'])
        inserted, error = self.run_replace(fake)
        self.assertIsNone(error)
        self.assertEqual(inserted, [[['가', '나']]])
        self.assertFalse(any(p.strip().startswith(('┌', '│', '└')) for p in fake.paras))

    def test_silent_failed_delete_is_retried_per_paragraph(self):
        fake = FakeHwp(['앞 문단'] + BOX + ['뒤 문단'], first_delete_fails=True)
        inserted, error = self.run_replace(fake)
        self.assertIsNone(error)
        self.assertEqual(len(inserted), 1)
        self.assertFalse(any(p.strip().startswith(('┌', '│', '└')) for p in fake.paras))
        self.assertIn('뒤 문단', fake.paras)                       # 정상 글은 지우지 않는다

    def test_never_deleted_means_no_table(self):
        fake = FakeHwp(['앞 문단'] + BOX + ['뒤 문단'], never_delete=True)
        inserted, error = self.run_replace(fake)
        self.assertIsNotNone(error)
        self.assertEqual(inserted, [])                            # 표와 잔여물이 함께 남지 않게 표를 넣지 않음


if __name__ == '__main__':
    unittest.main()
