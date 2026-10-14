"""설정 화면만 실제 설정 스키마로 빌드해 분류별 화면을 캡처한다(문서 처리는 하지 않는다).

결과: reports/flutter-ui/settings-<분류>.png. Flutter SDK와 Microsoft Edge(Playwright)가 필요하다.
"""
import argparse
import functools
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def profile_nodes(profile_json):
    """desktop_web_ui.format_profile('get')와 같은 모양으로 서식 요소 목록을 만든다."""
    from docfit_core import format_elements as elements
    profile = json.loads(Path(profile_json).read_text(encoding='utf-8'))
    analysis = profile.get('element_analysis') or {}
    nodes = []
    for path, _parent, label in elements.detail_nodes(analysis):
        fields = [{'key': key, 'label': elements.element_label(key),
                   'value': elements.format_value(key, item.get('value')),
                   'editable': elements.element_editable(key), 'choices': list(elements.element_choices(key))}
                  for key, item in elements.element_map(analysis, path).items()]
        if fields:
            nodes.append({'path': list(path), 'label': label, 'fields': fields})
    return {'id': 'preview', 'name': profile.get('name') or '서식 미리보기', 'revision': 'r',
            'coverage': {'total': len(nodes), 'applied': len(nodes)}, 'nodes': nodes}


def build(output, profile_json=None):
    from docfit_app.configuration_service import ConfigurationService

    class Store:
        def read(self):
            return {}
    data = profile_nodes(profile_json) if profile_json else ConfigurationService(Store()).snapshot()
    (ROOT / 'flutter_ui' / 'tool' / 'settings_preview_data.dart').write_text(
        "// 생성 파일: scripts/preview_settings.py\nconst previewSettingsJson = r'''"
        + json.dumps(data, ensure_ascii=False) + "''';\n", encoding='utf-8')
    flutter = os.environ.get('FLUTTER') or str(Path(os.environ['LOCALAPPDATA']) / 'DocFitTools/flutter/bin/flutter.bat')
    subprocess.run([flutter, 'build', 'web', '--release', '--no-pub', '--no-web-resources-cdn',
                    '--no-wasm-dry-run', '-t', 'tool/profile_preview.dart' if profile_json else 'tool/settings_preview.dart',
                    f'--output={output}'],
                   cwd=ROOT / 'flutter_ui', check=True, shell=os.name == 'nt')


def capture(web, categories, sizes, prefix='settings'):
    from playwright.sync_api import sync_playwright
    output = ROOT / 'reports' / 'flutter-ui'
    output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(SimpleHTTPRequestHandler, directory=str(web)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as p:
            sys.path.insert(0, str(ROOT / 'scripts'))
            from browser_qa import launch_browser
            browser = launch_browser(p)
            for width, height in sizes:
                page = browser.new_page(viewport={'width': width, 'height': height})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.wait_for_timeout(6000)
                page.screenshot(path=str(output / f'{prefix}-{width}.png'))
                for index in categories:
                    # 왼쪽 분류 타일을 차례로 누른다(좁은 화면은 위쪽 가로 목록).
                    if prefix == 'profile':
                        x, y = (200, 200 + 52 * index) if width >= 820 else (80 + 150 * index, 170)
                    else:
                        x, y = (150, 238 + 62 * index) if width >= 820 else (70 + 120 * index, 205)
                    page.mouse.click(x, y)
                    page.wait_for_timeout(700)
                    page.screenshot(path=str(output / f'{prefix}-{width}-{index}.png'))
            browser.close()
    finally:
        server.shutdown()
    print(json.dumps({'screenshots': str(output), 'page_errors': errors}, ensure_ascii=False))
    return not errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--profile', help='서식 프로필 JSON(element_analysis 포함)으로 서식 세부 편집 화면을 캡처')
    args = parser.parse_args()
    web = Path(tempfile.gettempdir()) / ('docfit-profile-preview' if args.profile else 'docfit-settings-preview')
    if not args.skip_build:
        build(web, args.profile)
    prefix = 'profile' if args.profile else 'settings'
    sys.exit(0 if capture(web, range(0, 9), [(1280, 860), (420, 860)], prefix) else 1)
