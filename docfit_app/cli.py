"""창을 띄우지 않는 파일 변환 명령줄."""
import argparse
import contextlib
import glob
import io
import json
import re
import sys
from pathlib import Path

COMMANDS = {'convert', 'help', 'version', 'formats'}
FORMAT_ORDER = ('hwpx', 'pdf', 'pdfz', 'pdfm', 'docx', 'epub', 'html', 'jpg', 'png', 'txt', 'md')


def attach_console():
    if sys.platform != 'win32':
        return bool(sys.stdout)
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        if not kernel.GetConsoleWindow() and not kernel.AttachConsole(-1):
            return False
        # python.exe의 파이프와 리디렉션은 보존하고 창 프로그램의 빈 스트림만 연다.
        for name in ('stdout', 'stderr'):
            stream = getattr(sys, name)
            if stream is None or stream is getattr(sys, '__' + name + '__') and getattr(sys, 'frozen', False):
                setattr(sys, name, open('CONOUT$', 'w', encoding='utf-8', buffering=1))
        return True
    except (OSError, AttributeError):
        return False


def notify(message):
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, '한글편집 후처리', 0x40)


class ArgumentError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)


def parser():
    from docfit_core.file_conversion import CONVERSION_OUTPUTS
    p = Parser(prog='HWP_AutoDocFit.exe')
    commands = p.add_subparsers(dest='command', required=True)
    convert = commands.add_parser('convert', help='파일·폴더·와일드카드 변환')
    convert.add_argument('inputs', nargs='+')
    convert.add_argument('--to', required=True, choices=[f for f in FORMAT_ORDER if f in CONVERSION_OUTPUTS])
    convert.add_argument('-o', '--output-dir')
    convert.add_argument('--json', action='store_true')
    convert.add_argument('--quiet', action='store_true')
    convert.add_argument('--notify', action='store_true')
    for name in ('help', 'version', 'formats'):
        commands.add_parser(name)
    return p


def expand_inputs(inputs):
    from docfit_core.file_conversion import CONVERSION_INPUTS
    files, seen = [], set()
    for value in inputs:
        matches = sorted(glob.glob(value)) if glob.has_magic(value) else [value]
        if not matches:
            raise ArgumentError(f'입력 파일이 없습니다: {value}')
        for match in matches:
            path = Path(match)
            if not path.exists() or path.is_symlink():
                raise ArgumentError(f'입력 파일이 없습니다(또는 심볼릭 링크): {match}')
            children = sorted(path.iterdir()) if path.is_dir() else [path]
            for child in children:
                if child.is_file() and not child.is_symlink() and child.suffix.lower() in CONVERSION_INPUTS:
                    key = str(child.resolve()).casefold()
                    if key not in seen:
                        seen.add(key)
                        files.append(str(child.resolve()))
                elif not path.is_dir():
                    raise ArgumentError(f'지원하지 않는 입력 형식: {child}')
    if not files:
        raise ArgumentError('변환할 입력 파일이 없습니다.')
    return files


def main(argv=None, *, stdout=None, stderr=None, runner=None, console=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    console = attach_console() if console is None else console
    stdout, stderr = stdout or sys.stdout or io.StringIO(), stderr or sys.stderr or io.StringIO()
    results, error, code = [], None, 0
    p = parser()
    try:
        args = p.parse_args(argv)
        if args.command == 'help':
            p.print_help(stdout)
            p._subparsers._group_actions[0].choices['convert'].print_help(stdout)
            return 0
        if args.command == 'version':
            version = getattr(sys.modules.get('__main__'), 'APP_VERSION', None)
            if version is None:
                source = (Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py').read_text(encoding='utf-8')
                version = re.search(r'^APP_VERSION = "([^"]+)"', source, re.M)[1]
            print(version, file=stdout)
            return 0
        if args.command == 'formats':
            from docfit_core.file_conversion import CONVERSION_OUTPUTS
            print(' '.join(f for f in FORMAT_ORDER if f in CONVERSION_OUTPUTS), file=stdout)
            return 0
        files = expand_inputs(args.inputs)
        if args.to == 'pdfm' and len(files) < 2:
            raise ArgumentError('PDF 합치기는 파일이 2개 이상 필요합니다.')
        if args.output_dir and Path(args.output_dir).exists() and not Path(args.output_dir).is_dir():
            raise ArgumentError('결과를 저장할 폴더 경로를 지정해 주세요.')
        if runner is None:
            from docfit_app.conversion_runner import run_conversion
            runner = run_conversion
        # 엔진의 진단 출력도 JSON 한 줄 규약을 깨지 않게 모은다.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            results = runner(files, args.to, output_dir=args.output_dir)
        statuses = {r['status'] for r in results}
        if 'failed' in statuses:
            code = 1
        elif 'success' not in statuses:
            code = 3
        elif 'skipped' in statuses:
            code = 1
    except SystemExit as exc:
        return int(exc.code or 0)
    except (ArgumentError, ValueError) as exc:
        code, error = 2, str(exc)
    except Exception as exc:
        code, error = 1, str(exc)
    if '--json' in argv:
        print(json.dumps(dict(exit_code=code, results=results, error=error), ensure_ascii=False), file=stdout)
    elif '--quiet' not in argv:
        if error:
            print(error, file=stderr)
        for result in results:
            print(f"{result['status']}: {result['source'] or ''} → {result['output'] or result['error']}", file=stdout)
    if '--notify' in argv and not console:
        failures = [r['error'] for r in results if r['status'] != 'success']
        notify(error or f"변환 완료: {sum(r['status'] == 'success' for r in results)}개\n" + '\n'.join(failures))
    return code
