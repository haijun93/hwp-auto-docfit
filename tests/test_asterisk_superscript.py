"""문두기호 문장의 단어 뒤 *, ** 위첨자 규칙을 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from docfit_core.asterisk_superscript import applies_to, mark_spans

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'


def marks(text):
    return [text[a:b] for a, b in mark_spans(text)]


class RuleTest(unittest.TestCase):
    def test_marks_after_a_word_in_marker_sentences(self):
        self.assertEqual(marks(' ㅇ (핵심 내용) 지자* 선행 투입 → 함대** 발진 → 지구도착 후 이주실행'), ['*', '**'])
        self.assertEqual(marks('□ 추진배경* 개요'), ['*'])
        self.assertEqual(marks('- 지자*와 함께**'), ['*', '**'])
        self.assertEqual(marks('ㅇ (추진)* 완료'), ['*'])       # 닫는 괄호도 단어 끝으로 본다
        self.assertEqual(marks('  ㅇ 단어*'), ['*'])            # 문장 끝

    def test_leading_marker_asterisks_and_other_uses_are_not_targets(self):
        for text in ('   * 양성자를 11차원으로 전개·가공하여 만든 초소형 지능체', '  ** 1차 선발대 발진 후 2차 본대를 발진한다.',
                     'ㅇ 3*4 계산', 'ㅇ a*b', 'ㅇ 단어 * 참고', 'ㅇ 단어*** 참고', 'ㅇ *앞', 'ㅇ 단어 **'):
            self.assertEqual(marks(text), [], text)

    def test_only_marker_sentences_apply(self):
        self.assertFalse(applies_to('단어* 참고'))
        self.assertTrue(applies_to(' ㅇ 단어* 참고'))
        self.assertEqual(marks('단어* 참고'), [])


class DocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _doc(self, body, extra_char=''):
        ns = self.ns
        header, _ = ns['제목_원본자료']()
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars))); base.set('id', '0'); base.set('height', '1500')
        chars.insert(0, base)
        section = f'<hs:sec {HS} {HP}>{body}</hs:sec>'.encode('utf-8')
        out = Path(tempfile.mkdtemp(prefix='docfit-sup-')) / 'in.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', section)
        return out

    @staticmethod
    def _p(*runs):
        inner = ''.join(f'<hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run>' for c, t in runs)
        return f'<hp:p id="1" paraPrIDRef="0" styleIDRef="0">{inner}</hp:p>'

    def _convert(self, body):
        ns = self.ns
        fn = ns['별표위첨자_hwpx_처리']
        source = self._doc(body)
        found = fn(source)
        target = source.with_name('out.hwpx')
        count = fn(source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        return source, found, count, header, section

    def _runs(self, section, index):
        p = [x for x in section if self.name(x) == 'p'][index]
        return [(''.join(t.text or '' for t in r if self.name(t) == 't'), r.get('charPrIDRef'))
                for r in p if self.name(r) == 'run']

    def test_example_document_marks_only_asterisks_after_words(self):
        body = (self._p(('0', '□ 보고 개요'))
                + self._p(('0', ' ㅇ (핵심 내용) 지자* 선행 투입 → 함대** 발진 → 지구도착 후 이주실행'))
                + self._p(('0', '   * 양성자를 11차원으로 전개·가공하여 만든 초소형 지능체'))
                + self._p(('0', '  ** 1차 선발대 발진 후 2차 본대를 발진한다.')))
        source, found, count, header, section = self._convert(body)
        self.assertEqual(found, {'Contents/section0.xml': [(1, 2)]})
        self.assertEqual(count, 2)
        runs = self._runs(section, 1)
        self.assertEqual([t for t, _ in runs], [' ㅇ (핵심 내용) 지자', '*', ' 선행 투입 → 함대', '**', ' 발진 → 지구도착 후 이주실행'])
        self.assertEqual(''.join(t for t, _ in runs), ' ㅇ (핵심 내용) 지자* 선행 투입 → 함대** 발진 → 지구도착 후 이주실행')
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        def sup(cid):
            return any(self.name(x) == 'supscript' for x in chars[cid])
        self.assertEqual([sup(c) for _, c in runs], [False, True, False, True, False])
        # 별표 글자모양은 주변과 위첨자 여부만 다르다(글꼴·크기·굵기·자간 그대로).
        plain = chars['0']
        star = chars[runs[1][1]]
        strip = lambda c: [(x.tag, dict(x.attrib)) for x in c if self.name(x) != 'supscript']
        self.assertEqual(strip(star), strip(plain))
        self.assertEqual({k: v for k, v in star.attrib.items() if k != 'id'}, {k: v for k, v in plain.attrib.items() if k != 'id'})
        self.assertEqual(runs[1][1], runs[3][1])            # *와 **가 같은 위첨자 글자모양을 공유
        self.assertEqual(int(next(x for x in header.iter() if self.name(x) == 'charProperties').get('itemCnt')),
                         len([x for x in header.iter() if self.name(x) == 'charPr']))
        # 문두기호로 쓴 * / **와 다른 문단은 그대로.
        self.assertEqual(self._runs(section, 2), [('   * 양성자를 11차원으로 전개·가공하여 만든 초소형 지능체', '0')])
        self.assertEqual(self._runs(section, 3), [('  ** 1차 선발대 발진 후 2차 본대를 발진한다.', '0')])
        self.assertEqual(self._runs(section, 0), [('□ 보고 개요', '0')])

    def test_is_idempotent_and_keeps_existing_superscript(self):
        body = self._p(('0', 'ㅇ 지자* 선행'))
        source, _, _, _, section = self._convert(body)
        fn = self.ns['별표위첨자_hwpx_처리']
        again = source.with_name('again.hwpx')
        # 결과를 다시 스캔하면 바꿀 것이 없다.
        result = source.with_name('out.hwpx')
        self.assertEqual(fn(result), {'Contents/section0.xml': []})
        self.assertEqual(fn(result, again, fn(result)), 0)

    def test_star_in_its_own_plain_run_is_switched_without_splitting(self):
        body = self._p(('0', 'ㅇ 지자'), ('0', '*'), ('0', ' 선행'))
        _, found, count, header, section = self._convert(body)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 1)]})
        runs = self._runs(section, 0)
        self.assertEqual([t for t, _ in runs], ['ㅇ 지자', '*', ' 선행'])
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        self.assertEqual([any(self.name(x) == 'supscript' for x in chars[c]) for _, c in runs], [False, True, False])

    def test_subscript_is_removed_when_superscripting_and_text_never_changes(self):
        ns = self.ns
        source = self._doc(self._p(('0', 'ㅇ 지자* 선행')))
        with zipfile.ZipFile(source) as z:
            header = z.read('Contents/header.xml')
        text_before = 'ㅇ 지자* 선행'
        fn = ns['별표위첨자_hwpx_처리']
        target = source.with_name('o.hwpx')
        fn(source, target, fn(source))
        with zipfile.ZipFile(target) as z:
            section = self.parse(z.read('Contents/section0.xml'))
        self.assertEqual(''.join(t for t, _ in self._runs(section, 0)), text_before)

    def test_pipeline_stage_reopens_only_when_needed(self):
        ns = self.ns
        stage = ns['별표위첨자_선행적용']
        opened = Mock(return_value=True)
        env = {'한글_문서_열기': opened, 'hwp': object(), '로그': Mock(), '중단_요청됨': lambda: False, '진단로그': Mock()}
        source = self._doc(self._p(('0', 'ㅇ 지자* 선행')))
        with patch.dict(stage.__globals__, env):
            notice = {}
            self.assertTrue(stage(str(source), 현재문서_기준=False, 변경알림=notice))
        self.assertTrue(notice['changed'])
        self.assertEqual(Path(opened.call_args.args[1]).name, 'asterisk.hwpx')
        opened.reset_mock()
        plain = self._doc(self._p(('0', 'ㅇ 별표 없음')))
        with patch.dict(stage.__globals__, dict(env, 한글_문서_열기=opened)):
            notice = {}
            self.assertTrue(stage(str(plain), 현재문서_기준=False, 변경알림=notice))
        self.assertFalse(notice['changed'])
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
