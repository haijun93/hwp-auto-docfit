"""창을 띄우지 않는 파일 변환 명령줄."""
import argparse
import contextlib
import glob
import io
import json
import math
import queue
import re
import threading
import time
import sys
from pathlib import Path

COMMANDS = {'convert', 'help', 'version', 'formats'}
ALIASES = {'--help': 'help', '-h': 'help', '/?': 'help', '--version': 'version'}


def is_cli_command(argv):
    return bool(argv and argv[0] in COMMANDS | ALIASES.keys() and not Path(argv[0]).exists())


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
    convert.add_argument('--timeout', type=float, default=180, help='파일당 제한 시간(초, 기본 180)')
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


def _run_with_timeout(runner, files, target, output_dir, timeout):
    """COM 생성부터 Quit까지 감시한다. 멈춘 COM 스레드는 기다리지 않는다."""
    from docfit_core.hwp_process import kill_owned
    messages = queue.Queue()
    stop = threading.Event()

    def work():
        try:
            result = runner(files, target, output_dir=output_dir,
                            progress=lambda event: messages.put(('event', event)), stop_event=stop)
            messages.put(('done', result))
        except BaseException as exc:
            messages.put(('error', exc))

    threading.Thread(target=work, daemon=True, name='docfit-cli-conversion').start()
    deadline, current, completed = time.monotonic() + timeout, files[0], []
    try:
        while True:
            try:
                kind, value = messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                stop.set()
                kill_owned()
                completed.append(dict(source=current, output=None, status='failed',
                                      error=f'시간 제한 {timeout:g}초 초과: 변환을 중단했습니다.'))
                return completed
            if kind == 'done':
                return value
            if kind == 'error':
                raise value
            if value[0] == 'doc_begin':
                current = files[value[1] - 1]
                deadline = time.monotonic() + timeout
            elif value[0] == 'saved':
                completed.append(dict(source=value[1], output=value[2], status='success', error=None))
            elif value[0] == 'document_error':
                from docfit_core.file_conversion import is_same_format
                completed.append(dict(source=value[1], output=None,
                                      status='skipped' if is_same_format(value[1], target) else 'failed', error=value[2]))
            elif value[0] == 'fatal_error':
                completed.append(dict(source=None, output=None, status='failed', error=value[1]))
            elif value[0] in {'file_conversion_finished', 'file_conversion_stopped'}:
                current = None
                deadline = time.monotonic() + timeout

    finally:
        stop.set()

def main(argv=None, *, stdout=None, stderr=None, runner=None, console=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ALIASES:
        argv[0] = ALIASES[argv[0]]
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
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ArgumentError('--timeout은 0보다 큰 유한한 초 값이어야 합니다.')
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
            results = _run_with_timeout(runner, files, args.to, args.output_dir, args.timeout)
        statuses = {r['status'] for r in results}
        if 'cancelled' in statuses:
            code, error = 130, '중단됨'
        elif 'failed' in statuses:
            code = 1
        elif 'success' not in statuses:
            code = 3
        elif 'skipped' in statuses:
            code = 1
    except KeyboardInterrupt:
        code, error = 130, '중단됨'
    except SystemExit as exc:
        return int(exc.code or 0)
    except (ArgumentError, ValueError) as exc:
        code, error = 2, str(exc)
    except Exception as exc:
        code, error = 1, str(exc)
    finally:
        from docfit_core.hwp_process import kill_owned
        kill_owned()
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
