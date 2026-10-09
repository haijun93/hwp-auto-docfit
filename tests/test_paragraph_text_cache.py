from pathlib import Path
import runpy
import unittest


class FakeHwp:
    """문단 글 읽기 횟수를 센다(InitScan 1회 = 실제 읽기 1회)."""

    def __init__(self):
        self.pos = (0, 3, 5)
        self.reads = 0

    def Run(self, name):
        if name == "MoveParaBegin":
            self.pos = (self.pos[0], self.pos[1], 0)
        return True

    def GetPos(self):
        return self.pos

    def SetPos(self, *pos):
        self.pos = tuple(pos)

    def InitScan(self, **kw):
        self.reads += 1

    def GetText(self):
        return 2, f"문단 {self.pos[1]}"

    def ReleaseScan(self):
        pass


class ParagraphTextCacheTest(unittest.TestCase):
    """알파 문단 글 캐시(2026-10-09): 같은 문단은 한 번만 읽고, 비우면 다시 읽고, 끄면 베타처럼 매번 읽는다."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def setUp(self):
        self.g = self.ns['현재문단_텍스트'].__globals__
        self.hwp = FakeHwp()
        self.g['hwp'] = self.hwp

    def tearDown(self):
        self.g['_문단글_캐시'] = None

    def test_cache_reads_once_per_paragraph_and_keeps_caret_at_paragraph_start(self):
        self.g['_문단글_캐시'] = {}
        읽기 = self.ns['현재문단_텍스트']
        self.assertEqual([읽기() for _ in range(9)], ['문단 3'] * 9)
        self.assertEqual(self.hwp.reads, 1)
        self.assertEqual(self.hwp.pos, (0, 3, 0))
        self.hwp.pos = (0, 4, 2)
        self.assertEqual(읽기(), '문단 4')
        self.assertEqual(self.hwp.reads, 2)

    def test_clearing_forces_fresh_read(self):
        self.g['_문단글_캐시'] = {}
        읽기 = self.ns['현재문단_텍스트']
        읽기()
        self.ns['_문단글_캐시_비우기']()
        읽기()
        self.assertEqual(self.hwp.reads, 2)

    def test_without_cache_reads_every_time(self):
        self.g['_문단글_캐시'] = None
        읽기 = self.ns['현재문단_텍스트']
        for _ in range(3):
            읽기()
        self.assertEqual(self.hwp.reads, 3)


if __name__ == '__main__':
    unittest.main()
