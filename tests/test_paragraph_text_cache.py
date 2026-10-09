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

    def test_edit_attempt_invalidates_even_when_edit_partly_fails(self):
        # R2: 지운 뒤 넣기만 실패해 수정 건수가 0이어도, 편집을 시도했으면 다음 읽기는 새로 읽는다.
        self.g['_문단글_캐시'] = {}
        읽기 = self.ns['현재문단_텍스트']
        읽기()
        self.ns['_문서_편집_시도']()          # hwp_run('Delete')·텍스트_삽입이 부르는 것과 같다
        읽기()
        self.assertEqual(self.hwp.reads, 2)

    def test_hwp_run_delete_bumps_edit_generation_but_moves_do_not(self):
        세대 = lambda: self.g['_문서_편집_세대']
        시작 = 세대()
        self.ns['hwp_run']('MoveLineEnd')
        self.assertEqual(세대(), 시작)
        self.ns['hwp_run']('Delete')
        self.assertEqual(세대(), 시작 + 1)

    def test_failed_read_is_not_cached_and_is_retried(self):
        # R4: 일시적 읽기 실패를 빈 문단으로 기억하지 않는다.
        self.g['_문단글_캐시'] = {}
        원래 = self.hwp.GetText
        실패 = {'남은': 1}
        def 가끔_실패():
            if 실패['남은']:
                실패['남은'] -= 1
                raise RuntimeError('일시 오류')
            return 원래()
        self.hwp.GetText = 가끔_실패
        self.assertEqual(self.ns['현재문단_텍스트'](), '문단 3')
        self.assertEqual(self.hwp.reads, 2)

    def test_without_cache_reads_every_time(self):
        self.g['_문단글_캐시'] = None
        읽기 = self.ns['현재문단_텍스트']
        for _ in range(3):
            읽기()
        self.assertEqual(self.hwp.reads, 3)


if __name__ == '__main__':
    unittest.main()
