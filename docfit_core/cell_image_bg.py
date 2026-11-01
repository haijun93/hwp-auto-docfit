"""표 셀 안의 이미지를 셀 테두리/배경의 배경 이미지(채우기 그림)로 변경한다.

- 표(hp:tbl) 셀(hp:tc) 안에 그림(hp:pic)만 단독으로 존재하는 셀이 대상이다.
- 글자와 그림이 함께 있거나 그림이 여러 개인 셀은 안전을 위해 건너뛴다.
- 채우기 유형은 "크기에 맞추어"(mode="TOTAL"), 문서에 포함(바이너리 참조 유지).
- 변환 후 원래 셀 안의 hp:pic 개체는 삭제하여 중복 표시를 방지한다.
- XML 파싱은 defusedxml만 사용한다.
"""
from __future__ import annotations

import copy
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"


def _tag_name(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _has_meaningful_text(tc_element) -> bool:
    """셀 안에 공백을 제외한 텍스트가 있는지 검사한다."""
    text = "".join(''.join(node.itertext()) for node in tc_element.iter(HP + "t")).strip()
    return len(text) > 0


def _get_cell_pics(tc_element) -> list:
    """셀 바로 안(하위 표 제외)에 있는 hp:pic 요소 목록을 찾는다."""
    pics = []

    def walk(node):
        for child in list(node):
            if child.tag == HP + "tbl":
                continue
            if child.tag == HP + "pic":
                pics.append(child)
            else:
                walk(child)

    walk(tc_element)
    return pics


def _find_border_fill(header_root, bf_id: str):
    border_fills = header_root.find(f".//{HH}borderFills")
    if border_fills is None:
        border_fills = header_root.find(f".//borderFills")
    if border_fills is None:
        return None, None
    for item in border_fills:
        if item.get("id") == str(bf_id):
            return border_fills, item
    return border_fills, None


def _create_img_brush_border_fill(header_root, base_bf_id: str, binary_item_id: str) -> str:
    """기존 borderFill의 테두리 속성을 복제하고 imgBrush 채우기를 설정한 새 borderFill을 추가한다."""
    parent, base = _find_border_fill(header_root, base_bf_id)
    if parent is None:
        raise ValueError("header.xml에 borderFills 요소가 없습니다.")

    if base is not None:
        new_bf = copy.deepcopy(base)
    else:
        new_bf = parent.makeelement(f"{HH}borderFill", {
            "threeD": "0",
            "shadow": "0",
            "centerLine": "NONE",
            "breakCellSeparateLine": "0",
        })

    # 새 고유 ID 계산
    max_id = 0
    for child in parent:
        try:
            cid = int(child.get("id", "0"))
            if cid > max_id:
                max_id = cid
        except (ValueError, TypeError):
            pass
    new_id = str(max_id + 1)
    new_bf.set("id", new_id)

    # 기존 fillBrush 찾거나 생성
    fill_brush = None
    for child in list(new_bf):
        if _tag_name(child) == "fillBrush":
            fill_brush = child
            break

    if fill_brush is None:
        fill_brush = new_bf.makeelement(f"{HC}fillBrush", {})
        new_bf.append(fill_brush)
    else:
        fill_brush.clear()

    # <hc:imgBrush mode="TOTAL"><hc:img binaryItemIDRef="BID_..." bright="0" contrast="0" effect="REAL_PIC" alpha="0"/></hc:imgBrush>
    img_brush = fill_brush.makeelement(f"{HC}imgBrush", {"mode": "TOTAL"})
    img_node = img_brush.makeelement(f"{HC}img", {
        "binaryItemIDRef": binary_item_id,
        "bright": "0",
        "contrast": "0",
        "effect": "REAL_PIC",
        "alpha": "0",
    })
    img_brush.append(img_node)
    fill_brush.append(img_brush)

    parent.append(new_bf)
    parent.set("itemCnt", str(len(parent)))
    return new_id


def convert_section_cell_images(section_root, header_root) -> int:
    """단일 섹션 XML과 header XML에서 표 셀 내 단독 이미지를 배경 이미지로 변환한다."""
    converted_count = 0

    for tbl in section_root.iter(HP + "tbl"):
        for tc in tbl.iter(HP + "tc"):
            if any(n.tag == HP + 'tbl' for n in tc.iter()):
                continue
            # 1. 셀 내 글자가 있으면 건너뜀
            if _has_meaningful_text(tc):
                continue

            # 2. 셀 내 그림(hp:pic) 개수 검사
            pics = _get_cell_pics(tc)
            if len(pics) != 1:
                continue

            pic = pics[0]
            # 3. 그림의 binaryItemIDRef 추출
            img_node = next((n for n in pic.iter() if _tag_name(n) == "img"), None)
            if img_node is None:
                continue
            bin_id = img_node.get("binaryItemIDRef")
            if not bin_id:
                continue

            base_bf_id = tc.get("borderFillIDRef", "1")
            try:
                # 4. 새 borderFill 생성 및 셀 참조 갱신
                new_bf_id = _create_img_brush_border_fill(header_root, base_bf_id, bin_id)
                tc.set("borderFillIDRef", new_bf_id)

                # 5. 셀 안에서 해당 hp:pic 개체 제거
                # 부모 노드를 찾아 pic 제거
                removed = False
                for parent in tc.iter():
                    if pic in list(parent):
                        parent.remove(pic)
                        removed = True
                        break

                if removed:
                    converted_count += 1
            except Exception:
                # 변환 실패 시 원래 그림을 그대로 보존한다.
                continue

    return converted_count


def convert_cell_images_to_bg_hwpx(hwpx_path: str | Path, output_path: str | Path | None = None) -> int:
    """HWPX 파일 안의 모든 표 셀 내 단독 이미지를 셀 배경 이미지로 변환한다.

    Returns:
        변환된 셀의 총 개수
    """
    source = Path(hwpx_path)
    target = Path(output_path) if output_path else source

    if not source.is_file() or source.suffix.lower() != ".hwpx":
        raise ValueError("올바른 .hwpx 파일 경로를 지정해 주세요.")

    import tempfile
    total_converted = 0

    from .table_catalog import _safe_archive
    with _safe_archive(source) as archive:
        namelist = archive.namelist()
        if "Contents/header.xml" not in namelist:
            return 0

        header_bytes = archive.read("Contents/header.xml")
        header_root = ET.fromstring(header_bytes)

        section_names = sorted(
            [n for n in namelist if re.fullmatch(r"Contents/section\d+\.xml", n)],
            key=lambda name: int(re.search(r"section(\d+)", name).group(1)),
        )

        modified_sections = {}
        for sec_name in section_names:
            sec_bytes = archive.read(sec_name)
            sec_root = ET.fromstring(sec_bytes)
            cnt = convert_section_cell_images(sec_root, header_root)
            if cnt > 0:
                total_converted += cnt
                modified_sections[sec_name] = ET.tostring(sec_root, encoding="utf-8", xml_declaration=True)

        if total_converted == 0:
            if target != source:
                import shutil
                shutil.copy2(source, target)
            return 0

        header_data = ET.tostring(header_root, encoding="utf-8", xml_declaration=True)

        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False, dir=target.parent) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as output:
                for info in archive.infolist():
                    if info.filename == "Contents/header.xml":
                        output.writestr(info, header_data)
                    elif info.filename in modified_sections:
                        output.writestr(info, modified_sections[info.filename])
                    else:
                        output.writestr(info, archive.read(info.filename))

            archive.close()
            tmp_path.replace(target)
        finally:
            tmp_path.unlink(missing_ok=True)

    return total_converted


# Aliases for backward compatibility and test contracts
convert_cell_images_to_background = convert_section_cell_images
convert_cell_images_in_archive = convert_cell_images_to_bg_hwpx
process_cell_image_to_bg = convert_cell_images_to_bg_hwpx

