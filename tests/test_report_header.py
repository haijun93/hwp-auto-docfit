import copy
import unittest

from defusedxml import ElementTree as ET

from docfit_core import report_header as RH

HH = "http://www.hancom.co.kr/hwpml/2011/head"
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HC = "http://www.hancom.co.kr/hwpml/2011/core"


def header(*chars):
    """chars: (id, 글꼴 id, 크기 pt). 글꼴 0=HY헤드라인M, 1=휴먼명조, 2=맑은 고딕."""
    shapes = "".join(f'<hh:charPr id="{i}" height="{int(pt * 100)}" textColor="#000000"><hh:fontRef hangul="{f}"/></hh:charPr>'
                     for i, f, pt in chars)
    return ET.fromstring(f'''<hh:head xmlns:hh="{HH}" xmlns:hc="{HC}"><hh:refList>
<hh:fontfaces><hh:fontface lang="HANGUL" fontCnt="3"><hh:font id="0" face="HY헤드라인M" type="TTF"/>
<hh:font id="1" face="휴먼명조" type="TTF"/><hh:font id="2" face="맑은 고딕" type="TTF"/></hh:fontface></hh:fontfaces>
<hh:borderFills itemCnt="2"><hh:borderFill id="1"/><hh:borderFill id="2"><hc:fillBrush><hc:winBrush faceColor="#F2F2F2"/></hc:fillBrush></hh:borderFill></hh:borderFills>
<hh:charProperties itemCnt="{len(chars)}">{shapes}</hh:charProperties>
<hh:paraProperties itemCnt="3"><hh:paraPr id="0"><hh:align horizontal="JUSTIFY"/></hh:paraPr>
<hh:paraPr id="1"><hh:align horizontal="CENTER"/></hh:paraPr><hh:paraPr id="2"><hh:align horizontal="RIGHT"/></hh:paraPr></hh:paraProperties>
</hh:refList></hh:head>''')


def p(text, char="1", para="0", extra=""):
    return f'<hp:p paraPrIDRef="{para}"><hp:run charPrIDRef="{char}">{extra}<hp:t>{text}</hp:t></hp:run></hp:p>'


def box(text_ps, fill="1"):
    return (f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:tbl rowCnt="1" colCnt="1"><hp:tr><hp:tc borderFillIDRef="{fill}">'
            f'<hp:subList>{text_ps}</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>')


def section(*items):
    return ET.fromstring(f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">{"".join(items)}</hs:sec>')


SECPR = '<hp:secPr id="sp"/>'


class InfoTests(unittest.TestCase):
    def test_roundtrip_of_government_bylines(self):
        for text in ("2026. 10. 7.  재정경제부  디지털정책과", "'26. 10. 7.(수)  /  디지털정책과",
                     "(2026. 10. 7., 과장 홍길동, ☎02-120-1234)", "2026년 10월 7일(수) 디지털정책과",
                     "문화예술과장 김○○ / 담당 이○○ (☎ 1234)", "문화경제국 문화예술과", "’26. 3. 5.(목) 경제정책국"):
            parsed = RH.parse_info(text)
            self.assertIsNotNone(parsed, text)
            self.assertEqual(RH.render_info(parsed["template"], parsed["date_format"], parsed["fields"]), text)

    def test_render_other_document_values_in_sample_style(self):
        sample = RH.parse_info("'26. 10. 7.(수)  /  디지털정책과")
        values = RH.parse_info("2025. 3. 2.  행정안전부  자치행정과")["fields"]
        self.assertEqual(RH.render_info(sample["template"], sample["date_format"], values),
                         "'25. 3. 2.(일)  /  행정안전부  /  자치행정과")
        person = RH.parse_info("(2026. 10. 7., 과장 홍길동, ☎02-120-1234)")
        self.assertEqual(RH.render_info(person["template"], person["date_format"], values),
                         "(2025. 3. 2., 행정안전부 자치행정과)")

    def test_empty_slots_are_not_written(self):
        dept_only = RH.parse_info("(디지털정책과)")
        self.assertEqual(RH.render_info(dept_only["template"], dept_only["date_format"], {"date": "2026-10-07"}), "")

    def test_body_sentences_are_not_bylines(self):
        for text in ("민원 대기 시간을 줄이기 위해 AI 안내 서비스를 단계적으로 도입", "가.민원 창구 대기 시간 장기화로 개선 필요"):
            self.assertIsNone(RH.parse_info(text), text)


class HeaderTests(unittest.TestCase):
    def sample(self):
        h = header(("0", "0", 20.0), ("1", "1", 15.0), ("2", "1", 12.0), ("3", "2", 14.0))
        sec = section(box(p("정부 보고서 제목 예시 문장입니다", char="0", para="1")),
                      p("2026. 10. 7.  재정경제부  디지털정책과", char="2", para="2"),
                      box(p("개요 첫 줄 내용", char="3") + p("개요 둘째 줄 내용", char="3"), fill="2"),
                      p("Ⅰ. 추진 배경"), p("□ 본문"))
        return h, sec

    def test_detects_1x1_title_box_byline_and_overview(self):
        h, sec = self.sample()
        found = RH.analyze(h, sec)
        self.assertEqual(found["title"]["container"], "table1x1")
        self.assertEqual(found["title"]["char"]["size_pt"], 20.0)
        self.assertEqual([i["text"] for i in found["info"]], ["2026. 10. 7.  재정경제부  디지털정책과"])
        self.assertEqual(found["info"][0]["align"], "RIGHT")
        self.assertTrue(found["overview"]["text"].startswith("개요 첫 줄"))

    def test_cover_title_is_skipped_for_body_head(self):
        h, _ = self.sample()
        sec = section(box(p("정부 보고서 제목 예시 문장입니다", char="0")), p("2026. 10. 7.", char="2"),
                      p("정부 보고서 제목 예시 문장입니다", char="0", para="1"), p("(2026. 10. 7., 과장 홍길동)", char="2"),
                      p("□ 본문"))
        found = RH.analyze(h, sec)
        self.assertTrue(found["title"]["cover"])
        self.assertEqual(found["title"]["container"], "paragraph")
        self.assertEqual([i["text"] for i in found["info"]], ["(2026. 10. 7., 과장 홍길동)"])

    def test_apply_copies_sample_layout_and_keeps_target_text_and_section_controls(self):
        sh, ssec = self.sample()
        spec = RH.build_spec(sh, ssec)
        th = header(("0", "1", 16.0), ("1", "1", 15.0), ("2", "1", 11.0))
        tsec = section(p("대상 문서의 제목 글입니다 확인용", char="0", para="1", extra=SECPR),
                       p("'25. 3. 2.(일) / 자치행정과", char="2", para="0"),
                       box(p("대상 개요 한 줄", char="1")), p("1. 본문"))

        def merge(target_header, sample_header):
            maps = {}
            for group in ("charProperties", "paraProperties", "borderFills"):
                dst = next(x for x in target_header.iter() if RH._tag(x) == group)
                src = next(x for x in sample_header.iter() if RH._tag(x) == group)
                maps[group] = {}
                for item in src:
                    clone = copy.deepcopy(item)
                    new = str(max(int(x.get("id")) for x in dst) + 1)
                    maps[group][item.get("id")] = new
                    clone.set("id", new)
                    dst.append(clone)
            return maps

        stats = RH.apply_header(th, tsec, spec, merge)
        self.assertEqual(stats["applied"], 1)
        got = RH.analyze(th, tsec)
        self.assertEqual(got["title"]["container"], "table1x1")
        self.assertEqual(got["title"]["text"], "대상 문서의 제목 글입니다 확인용")
        self.assertEqual(got["title"]["char"]["font"], "HY헤드라인M")
        self.assertEqual([i["text"] for i in got["info"]], ["2025. 3. 2.  자치행정과"])
        self.assertEqual(got["info"][0]["align"], "RIGHT")
        self.assertEqual(got["overview"]["text"], "대상 개요 한 줄")
        self.assertEqual(got["overview"]["box"]["fill"], "#F2F2F2")
        self.assertTrue(any(RH._tag(x) == "secPr" for x in tsec[0].iter()))   # 구역 정의 보존

    def test_date_cells_are_set_to_single_line(self):
        table = ET.fromstring(f'<hp:tbl xmlns:hp="{HP}" rowCnt="1" colCnt="2"><hp:tr>'
                              f'<hp:tc><hp:subList lineWrap="BREAK">{p("제목")}</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/></hp:tc>'
                              f'<hp:tc><hp:subList lineWrap="BREAK">{p("’26. 10. 10.(토)")}</hp:subList><hp:cellAddr colAddr="1" rowAddr="0"/></hp:tc>'
                              f'</hp:tr></hp:tbl>'.replace("<hp:p ", f'<hp:p xmlns:hp="{HP}" '))
        self.assertEqual(RH.squeeze_date_cells(table), 1)
        subs = [x for x in table.iter() if RH._tag(x) == "subList"]
        self.assertEqual([x.get("lineWrap") for x in subs], ["BREAK", "SQUEEZE"])


if __name__ == "__main__":
    unittest.main()
