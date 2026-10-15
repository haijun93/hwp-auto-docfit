"""학습 자료의 문서별 ID 독립성·평가군 중복 방지·역할 승인 검증."""
import copy
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree as ET
from docfit_core.style_learning import (table_fingerprint, build_learning_catalog,
                                       inspect_learning_document, learn_reviewed_data_table)
from tests.test_table_style import _header, _grid


def write_document(path, table, header=None):
    header = _header() if header is None else header
    section = ET.fromstring("<section/>")
    section.append(table)
    with ZipFile(path, "w") as z:
        z.writestr("Contents/header.xml", ET.tostring(header))
        z.writestr("Contents/section0.xml", ET.tostring(section))


class LearningTests(unittest.TestCase):
    def test_family_ignores_content_ids_and_repeated_body_rows(self):
        a, b = _grid(2, 2), _grid(5, 2, text=lambda r,c: "새 내용")
        ha, hb = _header(), _header()
        for e in hb.iter():
            if e.tag.endswith("}charPr") and e.get("id") == "0": e.set("id", "83")
        for e in b.iter():
            if e.get("charPrIDRef") == "0": e.set("charPrIDRef", "83")
        self.assertEqual(table_fingerprint(ha,a),table_fingerprint(hb,b))
        for e in hb.iter():
            if e.get("face") == "바탕": e.set("face", "돋움")
        self.assertNotEqual(table_fingerprint(ha,a),table_fingerprint(hb,b))

    def test_family_keeps_border_merge_and_width_ratio(self):
        h, a = _header(), _grid(2,2)
        for changed in ("border", "merge", "width"):
            b, hb = copy.deepcopy(a), copy.deepcopy(h)
            if changed == "border":
                next(e for e in hb.iter() if e.tag.endswith("}leftBorder")).set("type","DOUBLE_SLIM")
            elif changed == "merge":
                next(e for e in b.iter() if e.tag.endswith("}cellSpan")).set("colSpan","2")
            else:
                next(e for e in b.iter() if e.tag.endswith("}cellSz")).set("width","15000")
            self.assertNotEqual(table_fingerprint(h,a),table_fingerprint(hb,b),changed)

    def test_catalog_keeps_shared_family_in_one_split_without_text(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a=root/'기관A.hwpx';b=root/'기관B.hwpx'
            write_document(a,_grid(2,2,text=lambda r,c:'비공개 샘플내용'))
            write_document(b,_grid(5,2,text=lambda r,c:'다른 샘플내용'))
            result=build_learning_catalog([a,b],root=root)
            self.assertEqual(result['summary']['families'],1)
            self.assertEqual(result['summary']['split_groups'],1)
            self.assertEqual(result['families'][0]['source_count'],2)
            self.assertEqual(len({r['split'] for r in result['documents']}),1)
            self.assertTrue(result['warnings'])
            self.assertFalse(any(t['eligible'] for doc in result['documents'] for t in doc['tables']))
            self.assertNotIn('비공개 샘플내용',str(result))
            self.assertEqual(result,build_learning_catalog([b,a],root=root))

    def test_review_required_and_stale_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'sample.hwpx';write_document(path,_grid(2,2))
            candidate=inspect_learning_document(path)['tables'][0]
            with self.assertRaises(ValueError):learn_reviewed_data_table(path,candidate,approved_role='title')
            profile=learn_reviewed_data_table(path,candidate,approved_role='data')
            self.assertEqual(profile['table_style']['cols'],2)
            write_document(path,_grid(3,2))
            with self.assertRaises(ValueError):learn_reviewed_data_table(path,candidate,approved_role='data')

    def test_nested_and_box_are_not_general_table_training(self):
        with tempfile.TemporaryDirectory() as d:
            outer=_grid(2,2);inner=_grid(2,2)
            next(e for e in outer.iter() if e.tag.endswith('}run')).append(inner)
            p=Path(d)/'nested.hwpx';write_document(p,outer)
            r=inspect_learning_document(p)
            self.assertTrue(r['tables'][1]['nested'])
            self.assertEqual(r['tables'][0]['role'],'composite_form')
            with self.assertRaises(ValueError):learn_reviewed_data_table(p,r['tables'][0],approved_role='data')
            with self.assertRaises(ValueError):learn_reviewed_data_table(p,r['tables'][1],approved_role='data')
            write_document(p,_grid(1,1))
            c=inspect_learning_document(p)['tables'][0]
            self.assertEqual(c['role'],'box_or_title')
            with self.assertRaises(ValueError):learn_reviewed_data_table(p,c,approved_role='data')


if __name__=='__main__':unittest.main()
