"""Windows + 한/글에서 원본 사본으로 기존/알파 경로의 결과·시간을 비교한다."""

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import runpy
import shutil
import sys
from time import perf_counter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('documents', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='비어 있는 새 결과 폴더')
    parser.add_argument('--mode', choices=('format', 'all'), default='all')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Windows와 한/글 2020 COM이 필요합니다.')
    sources = [p.resolve(strict=True) for p in args.documents]
    # 기존 결과·원본을 덮어쓰지 않는다. 결과와 로그는 이 새 폴더에 보관한다.
    args.out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    from docfit_core.hwpx import inspect_hwpx, validate_hwpx

    namespace = runpy.run_path(str(repo / 'hwp-auto-docfit.py'), run_name='batch_smoke')
    execution = namespace['작업_실행']
    globals_ = execution.__globals__
    defaults = copy.deepcopy(namespace['_표준서식_설정_기본값'])
    report = []
    for index, source in enumerate(sources):
        before = sha256(source.read_bytes()).hexdigest()
        runs = {}
        for enabled, name in ((False, '기존'), (True, '알파')):
            folder = args.out / str(index) / name
            folder.mkdir(parents=True)
            copied = folder / source.name
            shutil.copy2(source, copied)
            globals_['표준서식_설정'] = copy.deepcopy(defaults)
            globals_['알파_HWPX_일괄서식_사용'] = enabled
            globals_['활성_정밀표_프로필'] = None
            globals_['활성_서식표_프로필'] = None
            globals_['활성_표서식_프로필'] = None
            while not globals_['gui_queue'].empty():
                globals_['gui_queue'].get_nowait()
            started = perf_counter()
            execution([str(copied)], 실행모드=args.mode, 표준서식=True, 검수=True, 자동닫기=True)
            seconds = perf_counter() - started
            events = []
            while not globals_['gui_queue'].empty():
                events.append(globals_['gui_queue'].get_nowait())
            outputs = [Path(event[2]) for event in events if event[0] == 'saved']
            errors = [event[0] for event in events if event[0] in ('document_error', 'fatal_error')]
            if errors or not outputs or not outputs[-1].is_file():
                raise RuntimeError(f'{name} 처리 실패: {source.name} / {errors}')
            output = outputs[-1]
            validate_hwpx(output)
            inspection = inspect_hwpx(output)
            runs[name] = {'seconds': round(seconds, 3), 'output': str(output),
                          'content_sha256': inspection.text_sha256,
                          'tables': inspection.table_count, 'images': inspection.image_count,
                          'xml_formatted': len(globals_['_표준서식_XML텍스트'])}
        unchanged = sha256(source.read_bytes()).hexdigest() == before
        same = all(runs['기존'][key] == runs['알파'][key] for key in ('content_sha256', 'tables', 'images'))
        report.append({'source': str(source), 'original_unchanged': unchanged,
                       'same_content_and_objects': same, 'runs': runs,
                       'speedup': round(runs['기존']['seconds'] / max(runs['알파']['seconds'], 0.001), 2)})
        (args.out / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if not unchanged:
            raise RuntimeError('원본 보존 검사 실패')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 속도 향상만으로 통과하지 않는다. 내용·표·그림 보존도 확인한다.
    return 0 if all(r['same_content_and_objects'] for r in report) else 1


if __name__ == '__main__':
    raise SystemExit(main())
