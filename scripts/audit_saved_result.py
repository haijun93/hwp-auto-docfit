"""Read-only HWP layout audit of a saved result, using a private COM instance."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    ns = runpy.run_path(str(root / 'hwp-auto-docfit.py'), run_name='saved_result_audit')
    document = args.document.resolve()
    if args.output.resolve() in {document, args.source.resolve() if args.source else document}:
        raise ValueError('Audit output must be separate from the input documents')
    digest = hashlib.sha256(document.read_bytes()).hexdigest()
    app = ns['win32'].DispatchEx('HwpFrame.HwpObject')
    checks = {}
    try:
        if not app.RegisterModule(ns['REGISTER_MODULE_NAME'], ns['REGISTER_MODULE_VALUE']):
            raise RuntimeError('Security module registration failed')
        app.XHwpWindows.Item(0).Visible = False
        if not app.Open(str(document), 'HWPX', 'forceopen:true'):
            raise RuntimeError('Cannot open result')
        ns['보고서_페이지배치_최종검사'].__globals__.update(
            hwp=app, 검수_사용=False, 현재_처리파일=str(document))
        checks['page_group'] = ns['보고서_페이지배치_최종검사']()
        checks['word_check'] = ns['보고서_단어분리_최종검사']()
        checks['control_word_check'] = ns['보고서_단어분리_최종검사'](컨트롤=True)
    finally:
        app.Clear(1)
        app.Quit()
    unchanged = hashlib.sha256(document.read_bytes()).hexdigest() == digest
    if not unchanged:
        raise RuntimeError('Input file changed during audit')
    report = {'document': str(document), 'sha256': digest, 'input_unchanged': unchanged,
              'checks': checks, 'scope': '페이지 배치 및 본문·컨트롤 화면줄의 의미 단위 분리',
              'unchecked': ['내어쓰기 정밀 위치', '전체 서식 준수', '짧은 마지막 줄 최적화']}
    if args.source:
        report['integrity'] = ns['compare_documents'](
            ns['inspect_hwpx'](args.source), ns['inspect_hwpx'](document))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
