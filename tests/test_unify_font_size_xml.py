"""서식 통일: 기본은 글꼴·크기만 맞추고('전체 서식 맞추기'는 옵션), 표본 조사는 HWPX에서 한다(알파, 2026-10-11)."""
from pathlib import Path
import runpy
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from zipfile import ZipFile

HEADER = ('<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"><hh:fontface lang="HANGUL">'
          '<hh:font id="0" face="함초롬바탕"/><hh:font id="1" face="굴림"/></hh:fontface><hh:charProperties>'
          '<hh:charPr id="0" height="1500"><hh:fontRef hangul="0"/></hh:charPr>'
          '<hh:charPr id="1" height="1200"><hh:fontRef hangul="1"/></hh:charPr></hh:charProperties></hh:head>')
PARAS = [(0, 'ㅇ 첫째 항목 문장입니다'), (0, ''), (1, 'ㅇ 둘째 항목 글꼴이 다른 문장입니다'), (0, 'ㅇ 셋째 항목 문장입니다')]


def make_hwpx(folder):
    body = ''.join(f'<hp:p><hp:run charPrIDRef="{char}"><hp:t>{text}</hp:t></hp:run></hp:p>' for char, text in PARAS)
    section = f'<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">{body}</hp:sec>'
    path = Path(folder) / 'doc.hwpx'
    with ZipFile(path, 'w') as archive:
        archive.writestr('Contents/header.xml', HEADER)
        archive.writestr('Contents/section0.xml', section)
    return path


class FakeHwp:
    def __init__(self, path, last):
        self.Path = str(path)
        self.index = 0
        self.last = last

    def SetPos(self, list_id, para, pos):
        self.index = para
        return True

    def GetPos(self):
        return (0, self.index, 0)

    def run(self, command):
        """MoveDocEnd·MoveDocBegin만 흉내 낸다(문단 번호 확인용)."""
        if command == "MoveDocEnd":
            self.index = self.last
        elif command == "MoveDocBegin":
            self.index = 0
        return True


class FontSizeOnlyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.g = cls.ns['_서식통일_글꼴크기만'].__globals__

    def test_default_compares_only_font_and_size_in_unify_mode(self):
        fn = self.ns['_서식통일_글꼴크기만']
        with patch.dict(self.g, {'작업_모드': 'unify', '선택_세부작업': None}):
            self.assertTrue(fn())
        with patch.dict(self.g, {'작업_모드': 'unify', '선택_세부작업': {'unify_full_format': True}}):
            self.assertFalse(fn())
        for mode in ('all', 'format', 'spacing'):
            with patch.dict(self.g, {'작업_모드': mode, '선택_세부작업': None}):
                self.assertFalse(fn(), mode)

    def test_representative_keeps_font_size_and_bold_only(self):
        fn = self.ns['_서식통일_글꼴크기_대표']
        대표 = {'font': ('함초롬바탕', 9), 'size': (1500, 9), 'marker_bold': (False, 9), 'label_bold': (True, 3),
              'color': ('#000000', 9), 'align': ('LEFT', 9), 'hanging_indent': (True, 4), 'italic': (False, 9)}
        self.assertEqual(sorted(fn(대표)), ['font', 'label_bold', 'marker_bold', 'size'])
        self.assertEqual(대표['color'], ('#000000', 9))      # 원본은 바꾸지 않는다
        self.assertEqual(fn(None), None)


class XmlSurveyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.fn = staticmethod(cls.ns['_서식통일_XML_조사'])
        cls.g = cls.fn.__globals__

    def survey(self, last=None, com_texts=None, pages=None, flag=True):
        with TemporaryDirectory() as temp:
            path = make_hwpx(temp)
            fake = FakeHwp(path, len(PARAS) - 1 if last is None else last)
            texts = com_texts or [text for _, text in PARAS]
            pages = pages or [1, 1, 2, 2]
            with patch.dict(self.g, {'hwp': fake, 'hwp_run': fake.run, '진단로그': Mock(),
                                     '_서식통일_HWPX_캐시': {}, '알파_서식통일_XML조사_사용': flag,
                                     '현재문단_텍스트': lambda: texts[fake.index],
                                     '현재_페이지번호': lambda: pages[fake.index],
                                     '중단_요청됨': lambda: False}):
                return self.fn()

    def test_samples_come_from_hwpx_without_walking_paragraphs(self):
        표본, 문맥, 위치텍스트, 첫쪽문단, 첫쪽끝 = self.survey()
        self.assertEqual(list(표본), ['ㅇ'])
        self.assertEqual([항목[1] for 항목 in 표본['ㅇ']], [(0, 0, 0), (0, 2, 0), (0, 3, 0)])
        self.assertEqual(문맥[(0, 2, 0)], 'ㅇ')
        self.assertEqual(위치텍스트[(0, 0, 0)], 'ㅇ 첫째 항목 문장입니다')
        self.assertEqual(표본['ㅇ'][1][0][0], '굴림')       # 글꼴이 다른 문장의 모양을 그대로 읽는다
        self.assertEqual((첫쪽문단, 첫쪽끝), ([0, 1], True))

    def test_single_page_document_has_no_first_page_end(self):
        결과 = self.survey(pages=[1, 1, 1, 1])
        self.assertEqual((결과[3], 결과[4]), ([0, 1, 2, 3], False))

    def test_paragraph_count_mismatch_falls_back(self):
        self.assertIsNone(self.survey(last=7))

    def test_text_mismatch_falls_back(self):
        self.assertIsNone(self.survey(com_texts=['다른 글', '', '다른 글', '다른 글']))

    def test_flag_off_falls_back(self):
        self.assertIsNone(self.survey(flag=False))


class XmlSurveyFlowTest(unittest.TestCase):
    """서식통일_전체_적용이 HWPX 조사로 표본을 모으고, 고칠 문장만 한/글 글을 다시 읽어 넘기는지."""

    def run_flow(self, flag):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        fn = ns['서식통일_전체_적용']
        paras = [(0, 'ㅇ 첫째 항목 문장입니다'), (0, 'ㅇ 둘째 항목 문장입니다'), (0, 'ㅇ 셋째 항목 문장입니다'),
                 (1, 'ㅇ 넷째 항목 글꼴이 다른 문장입니다')]
        applied, com_reads = [], []
        with TemporaryDirectory() as temp:
            body = ''.join(f'<hp:p><hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run></hp:p>' for c, t in paras)
            path = Path(temp) / 'doc.hwpx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('Contents/header.xml', HEADER)
                archive.writestr('Contents/section0.xml',
                                 f'<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">{body}</hp:sec>')
            fake = FakeHwp(path, len(paras) - 1)
            texts = [t for _, t in paras]

            def read():
                com_reads.append(fake.index)
                return texts[fake.index]

            def advance():
                if fake.index >= len(paras) - 1:
                    return False
                fake.index += 1
                return True

            settings = {
                'hwp': fake, 'hwp_run': fake.run, '중단_요청됨': lambda: False,
                '순회_시작': lambda: None, '쪽범위_안인가': lambda pos=None: True,
                '현재문단_텍스트': read, '현재_페이지번호': lambda: 1, '다음_문단으로_진행': advance,
                '문단_내어쓰기_기준_오프셋': lambda text: 2, '_서식통일_문서대표프로필': {},
                '_서식통일_자간보류문단': {}, '_서식통일_위치텍스트_보관': {}, '_서식통일_HWPX_캐시': {},
                '_서식통일_문단서식_적용': applied.append, '_서식통일_문단내어쓰기_적용': applied.append,
                '서식통일_빨간표시_사용': False, '서식통일_괄호크기차이': None, '서식통일_보류자간_재조정': lambda: True,
                '로그': Mock(), '진단로그': Mock(), '단계표시': Mock(), '작업_모드': 'unify', '선택_세부작업': None,
                '표준서식_사용': False, '괄호_축소_사용': False, '최종_내어쓰기_예정': False,
                '알파_서식통일_XML조사_사용': flag,
            }
            with patch.dict(fn.__globals__, settings):
                result = fn()
        return result, applied, com_reads

    def test_xml_survey_fixes_the_odd_font_sentence_and_reads_only_that_one_from_hangul(self):
        result, applied, com_reads = self.run_flow(True)
        self.assertTrue(result)
        fixed = [item for item in applied if isinstance(item, dict) and item['mismatch']]
        self.assertEqual([item['start'] for item in fixed], [(0, 3, 0)])
        self.assertEqual(fixed[0]['font'], '함초롬바탕')
        self.assertEqual(fixed[0]['text'], 'ㅇ 넷째 항목 글꼴이 다른 문장입니다')
        # 번호 확인용 3곳(첫·가운데·끝)과 고칠 문장 1곳만 한/글에서 읽는다(문단 4개를 모두 돌지 않는다).
        self.assertLessEqual(len(com_reads), 5)

    def test_result_is_the_same_as_the_old_paragraph_walk(self):
        _, xml_applied, _ = self.run_flow(True)
        _, walk_applied, _ = self.run_flow(False)
        pick = lambda items: [(item['start'], item['font'], item['size'], tuple(item['font_runs']))
                              for item in items if isinstance(item, dict) and item['mismatch']]
        self.assertEqual(pick(xml_applied), pick(walk_applied))


if __name__ == '__main__':
    unittest.main()
