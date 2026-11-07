#!/usr/bin/env python3
"""src/cp949_table.rs 생성기. 사용: python3 tools/gen_cp949.py > src/cp949_table.rs

CP949(통합완성형, UHC = KS X 1001 + 확장 한글 8,822자)의 2바이트 부분을 (앞바이트 0x81..=0xFE) x (뒤바이트 0x41..=0xFE)
격자로 펼쳐 유니코드 값(u16)을 적는다. 0은 '매핑 없음'. 값은 표준 매핑 사실(코드 -> 코드 포인트)이며
어떤 제3자 소스 코드도 복사하지 않는다. 표 값은 Python 표준 코덱 'cp949'에서 읽어 만든다(결과 17,048자).
"""
rows = []
count = 0
for lead in range(0x81, 0xFF):
    row = []
    for trail in range(0x41, 0xFF):
        try:
            c = bytes([lead, trail]).decode("cp949")
        except UnicodeDecodeError:
            row.append(0)
            continue
        assert len(c) == 1 and ord(c) < 0x10000
        row.append(ord(c))
        count += 1
    rows.append(row)
print("// 자동 생성 파일 - 직접 고치지 말고 tools/gen_cp949.py를 다시 실행한다.")
print("// CP949(UHC) 2바이트 -> 유니코드 표. 행 = 앞바이트 0x81..=0xFE, 열 = 뒤바이트 0x41..=0xFE, 0 = 매핑 없음.")
print(f"// 매핑 수: {count}")
print("pub const LEAD_MIN: u8 = 0x81;")
print("pub const LEAD_MAX: u8 = 0xFE;")
print("pub const TRAIL_MIN: u8 = 0x41;")
print("pub const TRAIL_MAX: u8 = 0xFE;")
print(f"pub const MAPPED: usize = {count};")
print(f"pub static TABLE: [[u16; {0xFE-0x41+1}]; {0xFE-0x81+1}] = [")
for row in rows:
    print("    [" + ",".join(f"{v:#06x}" if v else "0" for v in row) + "],")
print("];")
