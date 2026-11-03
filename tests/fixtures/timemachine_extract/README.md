# 타임머신 본문 추출기 시험용 소형 합성 Fixture

이 폴더의 파일들은 타임머신 본문 추출기의 단위 시험을 위한 최소 크기의 합성 파일입니다.
실제 사용자 문서나 기밀 문서를 포함하지 않으며, 각 형식의 표준 규격에 맞게 최소 바이너리/ZIP/텍스트로 생성되었습니다.

## 포함된 파일 목록
- `sample.txt`: UTF-8 일반 텍스트 (줄바꿈 및 행 번호 테스트)
- `sample_utf8_bom.txt`: UTF-8 BOM 텍스트
- `sample_utf16le.txt`: UTF-16 LE BOM 텍스트
- `sample_cp949.txt`: CP949 한글 인코딩 텍스트
- `sample.md`: 마크다운 텍스트
- `sample.eml`: RFC822 규격 이메일 메시지 (Subject, From, To 헤더 및 본문)
- `sample.hwpx`: HWPX 최소 규격 ZIP 아카이브 (header.xml, section0.xml)
- `sample.docx`: WordprocessingML 최소 규격 아카이브 (document.xml, header1.xml)
- `sample.pptx`: PresentationML 최소 규격 아카이브 (slide1.xml)
- `sample.xlsx`: SpreadsheetML 최소 규격 아카이브 (workbook.xml, sheet1.xml)
- `sample.pdf`: 1쪽 텍스트를 포함하는 최소 PDF 바이너리
