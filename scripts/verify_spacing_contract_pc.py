"""실제 한/글에서 자간 정리의 원문 보존·본문/표 어절 분리를 검증한다.

입력 원본은 사본으로 처리한다. TXT는 변환 직후 HWPX를 원문 대조 기준으로
보관한다. 사용자 설정 파일을 바꾸지 않고 이 시험의 자간·단어 검사만 켠다.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))


def paragraph_texts(path):
    """문단별 표시 텍스트. 중첩 표 본문은 해당 칸 문단에서 한 번만 읽는다."""
    hp = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
    result = []
    with ZipFile(path) as archive:
        for name in sorted(n for n in archive.namelist()
                           if n.startswith('Contents/section') and n.endswith('.xml')):
            root = ET.fromstring(archive.read(name))
            for paragraph in root.iter(hp + 'p'):
                parts = []
                for run in paragraph.findall(hp + 'run'):
                    for node in run:
                        if node.tag == hp + 't':
                            parts.append(node.text or '')
                            for child in node:
                                kind = child.tag.rsplit('}', 1)[-1]
                                parts.append({'tab': '\t', 'fwSpace': ' ', 'nbSpace': ' ',
                                              'lineBreak': '\n'}.get(kind, ''))
                                parts.append(child.tail or '')
                        elif node.tag == hp + 'tab':
                            parts.append('\t')
                result.append(''.join(parts))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    source = args.document.resolve()
    if not source.is_file():
        parser.error('입력 파일이 없습니다.')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / 'work'
    work.mkdir()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    import pythoncom
    import regression_pc as rp
    pythoncom.CoInitialize()
    try:
        g = rp.앱_불러오기()
        settings = copy.deepcopy(g['설정_불러오기']())
        settings.update(verify=True, spacing_exclude_tables=False, table_spacing=True,
                        two_pass_processing=False)
        enabled = {'reset_spacing', 'body_spacing', 'short_line', 'control_spacing',
                   'control_short_line', 'word_check', 'control_word_check'}
        from docfit_core.stage_selection import stages_for_mode
        settings.setdefault('stage_choices', {})['spacing'] = {
            key: key in enabled for key, _ in stages_for_mode('spacing')}
        g['설정_불러오기'] = lambda: copy.deepcopy(settings)
        snapshot = out / 'input.hwpx'
        if source.suffix.lower() == '.hwpx':
            shutil.copyfile(source, snapshot)
        else:
            converter = g['외부문서_hwpx로_변환']
            def capture(original, suffix, target):
                result = converter(original, suffix, target)
                shutil.copyfile(target, snapshot)
                return result
            g['외부문서_hwpx로_변환'] = capture
        with (out / 'processing.log').open('w', encoding='utf-8') as log:
            _, result, seconds, score, run_settings = rp.처리(
                g, str(source), work, 'spacing', False, log, 검수_강제=True)
        if result is None or not snapshot.is_file():
            raise RuntimeError('변환 직후 원문 또는 결과 파일이 없습니다.')
        kept = out / 'result.hwpx'
        shutil.copyfile(result, kept)
        checks = (g.get('최종검수_문서목록') or [{}])[-1].get('rule_checks', {})
        required = ('word_check', 'control_word_check')
        same = paragraph_texts(snapshot) == paragraph_texts(kept)
        unchanged = hashlib.sha256(source.read_bytes()).hexdigest() == digest
        passed = same and unchanged and all(checks.get(k, {}).get('status') == 'passed'
                                            for k in required)
        report = {'status': 'pass' if passed else 'fail', 'source': str(source),
                  'source_sha256': digest, 'source_unchanged': unchanged,
                  'visible_paragraph_texts_equal': same, 'seconds': seconds,
                  'work_score': score, 'settings': run_settings, 'checks': checks,
                  'scope': '자간 정리 전후 표시 텍스트 및 저장 후 본문·표/컨트롤 어절 분리',
                  'unchecked': ['원본 대비 전체 시각적 동일성', '전체 서식 재연']}
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    finally:
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    raise SystemExit(main())
