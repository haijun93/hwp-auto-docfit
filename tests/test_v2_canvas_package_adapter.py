"""In-memory package merging and failure atomicity regressions."""
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import warnings
from unittest.mock import patch
from zipfile import ZipFile, ZIP_STORED

from defusedxml import ElementTree as ET
from docfit_core.hwpx.canvas_hwpx_builder import HP, HH, HC
from docfit_core.hwpx.canvas_package_adapter import merge_canvas_block_into_hwpx as merge
from tests.test_v2_canvas_hwpx import sketch, graph, tree


def fixture(extra=None):
    header = f'''<hh:head xmlns:hh="{HH[1:-1]}" xmlns:hc="{HC[1:-1]}"><hh:refList>
      <hh:borderFills itemCnt="2"><hh:borderFill id="1"/><hh:borderFill id="19"/></hh:borderFills>
      <hh:charProperties itemCnt="1"><hh:charPr id="7" height="1000"/></hh:charProperties>
      <hh:paraProperties itemCnt="1"><hh:paraPr id="13"><hh:align horizontal="JUSTIFY" vertical="BASELINE"/>
      <hh:margin><hc:right value="42"/></hh:margin></hh:paraPr></hh:paraProperties>
      <hh:styles itemCnt="1"><hh:style id="5" paraPrIDRef="13" charPrIDRef="7"/></hh:styles>
    </hh:refList></hh:head>'''
    section = f'''<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP[1:-1]}">
      <hp:p id="10" paraPrIDRef="13" styleIDRef="5"><hp:run charPrIDRef="7"><hp:t>original</hp:t></hp:run></hp:p>
      <hp:p id="11" paraPrIDRef="13" styleIDRef="5"><hp:run charPrIDRef="7"><hp:t>end</hp:t></hp:run></hp:p>
    </hs:sec>'''
    members = {'mimetype': b'application/hwp+zip', 'Contents/header.xml': header.encode(),
               'Contents/section0.xml': section.encode(), 'BinData/preserve.bin': b'\x00\xfforiginal'}
    members.update(extra or {})
    stream = BytesIO()
    with ZipFile(stream, 'w', compression=ZIP_STORED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return stream.getvalue()


def roots(data):
    with ZipFile(BytesIO(data)) as archive:
        assert archive.testzip() is None
        return (ET.fromstring(archive.read('Contents/header.xml')),
                ET.fromstring(archive.read('Contents/section0.xml')))


class CanvasPackageTests(unittest.TestCase):
    def test_table_remaps_sparse_ids_and_clones_formatting(self):
        data = fixture()
        header, section = roots(merge(data, dict(kind='table_sketch', source=sketch(), after_id='10')))
        self.assertEqual([''.join(p.itertext()).strip() for p in (section[0], section[-1])], ['original', 'end'])
        table = section[1].find(HP+'run/'+HP+'tbl')
        self.assertIsNotNone(table)
        cells = table.findall('.//'+HP+'tc')
        self.assertEqual([c.get('borderFillIDRef') for c in cells], ['20', '21', '22'])
        pool = header.find('.//'+HH+'charProperties')
        self.assertEqual([n.get('id') for n in pool], ['7', '8', '9'])
        self.assertEqual(pool[-1].get('height'), '1000')
        self.assertIsNotNone(pool[-1].find(HH+'bold'))
        self.assertEqual(table.find('.//'+HP+'run').get('charPrIDRef'), '9')
        for name in ('borderFills', 'charProperties', 'paraProperties', 'styles'):
            pool = header.find('.//'+HH+name)
            self.assertEqual(int(pool.get('itemCnt')), len(pool))
        self.assertEqual(data, fixture())

    def test_diagram_global_ids_include_other_sections(self):
        extra = {'Contents/section1.xml': f'<hp:p xmlns:hp="{HP[1:-1]}" id="900"/>'.encode()}
        data = fixture(extra)
        merged = merge(data, dict(kind='diagram', source=graph()))
        _, section = roots(merged)
        generated = section[-1]
        ids = [int(n.get('id')) for n in generated.iter() if 'id' in n.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreater(min(ids), 900)
        for node in generated.iter():
            if 'instid' in node.attrib:
                self.assertEqual(node.get('id'), node.get('instid'))
        with ZipFile(BytesIO(merged)) as archive:
            self.assertEqual(archive.read('Contents/section1.xml'), extra['Contents/section1.xml'])
            self.assertEqual(archive.read('BinData/preserve.bin'), b'\x00\xfforiginal')
            self.assertEqual(archive.infolist()[0].compress_type, ZIP_STORED)

    def test_mindmap_outline_and_summary(self):
        for mode in ('outline', 'summary_table'):
            header, section = roots(merge(fixture(), dict(kind='mindmap', source={**tree(), 'mode': mode})))
            paragraphs = [p for node in list(section)[2:] for p in node.iter(HP+'p')]
            self.assertEqual([''.join(p.itertext()) for p in paragraphs if p.find(HP+'run/'+HP+'t') is not None],
                             ['1\troot', '1.1\tA', '1.1.1\tB', '1.2\tC'])
            pool = header.find('.//'+HH+'paraProperties')
            self.assertEqual(len(pool), 33)
            self.assertEqual(pool[3].find(HH+'margin/'+HC+'left').get('value'), '7200')
            self.assertEqual(pool[3].find(HH+'margin/'+HC+'right').get('value'), '42')
            refs = {p.get('paraPrIDRef') for p in paragraphs}
            self.assertTrue({'14', '15', '16'}.issubset(refs))

    def test_repeated_merge_allocates_fresh_ids(self):
        data = fixture()
        for kind, payload in [('table_sketch', sketch()), ('mindmap', tree()), ('diagram', graph())]*2:
            data = merge(data, dict(kind=kind, source=payload))
        header, section = roots(data)
        ids = [n.get('id') for n in section.iter() if 'id' in n.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        for pool in header.find(HH+'refList'):
            ids = [n.get('id') for n in pool]
            self.assertEqual(len(ids), len(set(ids)))

    def test_rejects_invalid_archives_xml_and_anchors(self):
        for data in (b'not zip', fixture()[:-15],
                     fixture({'Contents/header.xml': b'<broken>'}),
                     fixture({'../escape': b'bad'}),
                     fixture({'Contents/header.xml': b'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>'})):
            with self.subTest(data=data[:10]), self.assertRaises(ValueError):
                merge(data, dict(kind='diagram', source=graph()))
        for block in (dict(kind='unknown', source={}), dict(kind='diagram', source=graph(), after_id='missing')):
            with self.assertRaises(ValueError):
                merge(fixture(), block)

    def test_atomic_output_original_protection_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'source.hwpx', Path(directory)/'out.hwpx'
            source.write_bytes(fixture())
            target.write_bytes(b'previous output')
            block = dict(kind='diagram', source=graph())
            with self.assertRaises(ValueError):
                merge(source, block, source)
            with patch('docfit_core.hwpx.canvas_package_adapter.os.replace', side_effect=OSError('locked')):
                with self.assertRaises(OSError):
                    merge(source, block, target)
            self.assertEqual(target.read_bytes(), b'previous output')
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['out.hwpx', 'source.hwpx'])
            result = merge(source, block, target)
            self.assertEqual(target.read_bytes(), result)
            self.assertEqual(source.read_bytes(), fixture())
            roots(result)

    def test_duplicate_crc_and_dangling_references(self):
        duplicate = BytesIO(fixture())
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with ZipFile(duplicate, 'a') as archive:
                archive.writestr('Contents/header.xml', b'<duplicate/>')
        corrupt = fixture().replace(b'\x00\xfforiginal', b'\x00\xffcorrupted', 1)
        with ZipFile(BytesIO(fixture())) as archive:
            section = archive.read('Contents/section0.xml')
        dangling = fixture({'Contents/section0.xml': section.replace(b'charPrIDRef="7"', b'charPrIDRef="99"')})
        for data in (duplicate.getvalue(), corrupt, dangling):
            with self.assertRaises(ValueError):
                merge(data, dict(kind='mindmap', source=tree()))

    def test_validation_failure_does_not_promote(self):
        from docfit_core.hwpx import canvas_package_adapter as adapter
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'out.hwpx'
            target.write_bytes(b'previous')
            real_read = adapter._read_package
            calls = 0

            def fail_final_read(data):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise ValueError('failed final validation')
                return real_read(data)

            with patch.object(adapter, '_read_package', side_effect=fail_final_read):
                with self.assertRaises(ValueError):
                    merge(fixture(), dict(kind='mindmap', source=tree()), target)
            self.assertEqual(target.read_bytes(), b'previous')
            self.assertEqual(list(Path(directory).iterdir()), [target])


if __name__ == '__main__':
    unittest.main()
