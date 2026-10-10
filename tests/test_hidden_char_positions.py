"""숨은 글자(고정폭 빈칸 등)가 있는 문단에서 글 정리 규칙이 다른 글자를 지우지 않는다(test6 시험 P1, 2026-10-10).

한/글 GetText는 고정폭 빈칸을 돌려주지 않는데 커서 위치는 차지한다. 예전에는 '구비2,241,275천원,(고정폭)재원'의
쉼표 공백 보정이 한 칸 밀려 '원'을 지우고 쉼표를 넣었다('천, ,').
"""
from pathlib import Path
import runpy
import unittest

HIDDEN = "\x01"      # 가짜 한/글에서 고정폭 빈칸 자리(GetText가 돌려주지 않음)


class FakeHwp:
    def __init__(self, chars):
        self.chars = list(chars)
        self.pos = 0
        self.sel = None

    # 위치
    def GetPos(self):
        return (0, 0, self.pos)

    def SetPos(self, l, p, o):
        self.pos = max(0, min(o, len(self.chars)))
        self.sel = None
        return True

    def SelectText(self, sp, so, ep, eo):
        self.sel = (so, eo)
        self.pos = eo
        return True

    def run(self, action):
        if action == "MoveParaBegin":
            self.pos = 0
        elif action == "MoveParaEnd":
            self.pos = len(self.chars)
        elif action == "MoveSelParaEnd":
            self.sel = (self.pos, len(self.chars))
        elif action == "Cancel":
            self.sel = None
        elif action == "Delete":
            if self.sel:
                a, b = self.sel
                del self.chars[a:b]
                self.pos, self.sel = a, None
            else:
                del self.chars[self.pos:self.pos + 1]
        return True

    def Run(self, action):
        return self.run(action)

    # 글 읽기(선택 범위의 보이는 글만)
    def InitScan(self, **kw):
        return True

    def GetText(self):
        a, b = self.sel if self.sel else (self.pos, len(self.chars))
        return 2, "".join(c for c in self.chars[a:b] if c != HIDDEN)

    def ReleaseScan(self):
        return True

    def insert(self, text):
        self.chars[self.pos:self.pos] = list(text)
        self.pos += len(text)

    def visible(self):
        return "".join(c for c in self.chars if c != HIDDEN)

    def raw(self):
        return "".join(self.chars)


class HiddenCharPositionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def run_rule(self, raw, rule):
        fake = FakeHwp(raw)
        g = self.ns[rule].__globals__
        saved = {k: g[k] for k in ('hwp', 'hwp_run', '텍스트_삽입', '현재_한칸표인가', '진단로그', '로그', '_문단글_캐시')}
        try:
            g.update(hwp=fake, hwp_run=fake.run, 텍스트_삽입=fake.insert, 현재_한칸표인가=lambda: False,
                     진단로그=lambda *a: None, 로그=lambda *a: None, _문단글_캐시=None)
            g['_문단_위치표_저장'].clear()
            self.ns[rule]()
        finally:
            g.update(saved)
        return fake

    def test_comma_rule_does_not_eat_unit_after_hidden_space(self):
        # 앞쪽 쉼표 뒤 고정폭 빈칸(GetText에 없음)이 뒤쪽 위치를 한 칸 밀던 경우(실측 문장 구조)
        fake = self.run_rule("국비," + HIDDEN + "구비2,241,275천원,재원", '쉼표_공백_정리_문단_처리')
        self.assertIn("275천원, 재원", fake.visible())
        self.assertNotIn("천, ,", fake.visible())

    def test_colon_rule_after_hidden_space_keeps_time(self):
        fake = self.run_rule("시" + HIDDEN + "간 15:00 비고 :내용", '콜론_공백_정리_문단_처리')
        self.assertIn("15:00", fake.visible())
        self.assertIn("비고: 내용", fake.visible())

    def test_paragraph_without_hidden_chars_is_unchanged_behavior(self):
        fake = self.run_rule("도토리 ,만두", '쉼표_공백_정리_문단_처리')
        self.assertEqual(fake.visible(), "도토리, 만두")

    def test_position_map(self):
        fake = FakeHwp("가" + HIDDEN + "나다")
        g = self.ns['문단_위치'].__globals__
        saved = {k: g[k] for k in ('hwp', 'hwp_run', '_최근_문단글')}
        try:
            g.update(hwp=fake, hwp_run=fake.run, _최근_문단글=((0, 0), "가나다"))
            g['_문단_위치표_저장'].clear()
            위치 = self.ns['문단_위치']
            self.assertEqual([위치((0, 0, 0), i) for i in range(4)], [0, 2, 3, 4])
            self.assertEqual(위치((0, 0, 0), 1, 끝쪽=True), 1)     # '가' 바로 뒤(숨은 글자 앞)
        finally:
            g.update(saved)


if __name__ == '__main__':
    unittest.main()
