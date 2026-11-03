"""소형 합성 fixture 생성기."""
from __future__ import annotations

import codecs
from pathlib import Path
from zipfile import ZipFile

FIXTURES_DIR = Path(__file__).resolve().parent


def generate_all_fixtures():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. sample.txt (UTF-8)
    (FIXTURES_DIR / "sample.txt").write_text("첫 번째 줄 텍스트입니다.\n\n세 번째 줄 텍스트입니다.\n", encoding="utf-8")

    # 2. sample_utf8_bom.txt
    (FIXTURES_DIR / "sample_utf8_bom.txt").write_bytes(
        codecs.BOM_UTF8 + "BOM이 포함된 UTF-8 일반 텍스트 문서입니다.\n두 번째 줄입니다.\n".encode("utf-8")
    )

    # 3. sample_utf16le.txt
    (FIXTURES_DIR / "sample_utf16le.txt").write_bytes(
        codecs.BOM_UTF16_LE + "UTF-16 LE 인코딩 본문입니다.\n두 번째 줄입니다.\n".encode("utf-16-le")
    )

    # 4. sample_cp949.txt
    (FIXTURES_DIR / "sample_cp949.txt").write_bytes(
        "CP949 인코딩으로 작성된 한글 문서입니다.\n두 번째 줄입니다.\n".encode("cp949")
    )

    # 5. sample.md
    (FIXTURES_DIR / "sample.md").write_text(
        "# 타임머신 마크다운 시험 문서\n\n이 문서는 마크다운 본문 추출 시험용입니다.\n\n- 항목 1\n- 항목 2\n",
        encoding="utf-8",
    )

    # 6. sample.hwpx
    hwpx_path = FIXTURES_DIR / "sample.hwpx"
    with ZipFile(hwpx_path, "w") as arc:
        arc.writestr("Contents/header.xml", '<?xml version="1.0" encoding="UTF-8"?><hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"/>')
        arc.writestr(
            "Contents/section0.xml",
            '<?xml version="1.0" encoding="UTF-8"?><hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
            '<hp:p><hp:t>타임머신 섹션0 문단 1</hp:t></hp:p>'
            '<hp:p><hp:t>섹션0 문단 2 내용</hp:t></hp:p>'
            '</hp:sec>',
        )
        arc.writestr(
            "Contents/section1.xml",
            '<?xml version="1.0" encoding="UTF-8"?><hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
            '<hp:p><hp:t>섹션1 첫 번째 문단</hp:t></hp:p>'
            '</hp:sec>',
        )

    # 7. sample.docx
    docx_path = FIXTURES_DIR / "sample.docx"
    with ZipFile(docx_path, "w") as arc:
        arc.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>워드 본문 첫 번째 문단</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>워드 본문 두 번째 문단</w:t></w:r></w:p>'
            '</w:body></w:document>',
        )
        arc.writestr(
            "word/header1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:p><w:r><w:t>워드 머리글 영역 내용</w:t></w:r></w:p>'
            '</w:hdr>',
        )

    # 8. sample.pptx
    pptx_path = FIXTURES_DIR / "sample.pptx"
    with ZipFile(pptx_path, "w") as arc:
        arc.writestr(
            "ppt/slides/slide1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:sp><p:txBody>'
            '<a:p><a:r><a:t>슬라이드 1 제목 문단</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld></p:sld>',
        )
        arc.writestr(
            "ppt/slides/slide2.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:sp><p:txBody>'
            '<a:p><a:r><a:t>슬라이드 2 설명 문단</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld></p:sld>',
        )

    # 9. sample.xlsx
    xlsx_path = FIXTURES_DIR / "sample.xlsx"
    with ZipFile(xlsx_path, "w") as arc:
        arc.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets>'
            '<sheet name="매출현황" sheetId="1" r:id="rId1"/>'
            '<sheet name="지출현황" sheetId="2" r:id="rId2"/>'
            '</sheets></workbook>',
        )
        arc.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
            '</Relationships>',
        )
        arc.writestr(
            "xl/sharedStrings.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="3" uniqueCount="3">'
            '<si><t>품목명</t></si>'
            '<si><t>수량</t></si>'
            '<si><t>단가</t></si>'
            '</sst>',
        )
        arc.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c></row>'
            '<row r="2"><c r="A2" t="inlineStr"><is><t>노트북</t></is></c><c r="B2"><v>10</v></c><c r="C2"><v>1500000</v></c></row>'
            '</sheetData></worksheet>',
        )
        arc.writestr(
            "xl/worksheets/sheet2.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            '<row r="1"><c r="A1" t="inlineStr"><is><t>운반비</t></is></c><c r="B1"><v>50000</v></c></row>'
            '</sheetData></worksheet>',
        )

    # 10. sample.pdf (최소 1페이지 표준 PDF 바이너리)
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 53 >>\nstream\n"
        b"BT\n/F1 24 Tf\n100 700 Td\n(TimeMachine PDF Page 1 Content) Tj\nET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000244 00000 n \n"
        b"0000000347 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n424\n%%EOF\n"
    )
    (FIXTURES_DIR / "sample.pdf").write_bytes(pdf_content)

    # 11. sample.eml (RFC 표준 multipart 이메일 메시지)
    eml_content = (
        "From: sender@example.com\n"
        "To: receiver@example.com\n"
        "Subject: =?UTF-8?B?7Jew6rCEIOyXheustCDrs7Tqs6DshJwg7KCc7Lac?=\n"
        "MIME-Version: 1.0\n"
        'Content-Type: multipart/mixed; boundary="BOUNDARY_12345"\n\n'
        "--BOUNDARY_12345\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: 8bit\n\n"
        "안녕하세요.\n"
        "2026년 업무 추진 실적 보고서입니다.\n"
        "확인 부탁드립니다.\n\n"
        "--BOUNDARY_12345\n"
        'Content-Type: application/octet-stream; name="data.bin"\n'
        'Content-Disposition: attachment; filename="data.bin"\n'
        "Content-Transfer-Encoding: base64\n\n"
        "AQIDBAUGBwg=\n"
        "--BOUNDARY_12345--\n"
    )
    (FIXTURES_DIR / "sample.eml").write_text(eml_content, encoding="utf-8")


if __name__ == "__main__":
    generate_all_fixtures()
