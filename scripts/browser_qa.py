"""설치된 브라우저로 실행하는 비표시 QA; 사용자 브라우저 세션에는 연결하지 않는다."""
import os
from pathlib import Path
import sys


def launch_browser(playwright):
    explicit = os.environ.get('DOCFIT_QA_BROWSER_PATH')
    if explicit:
        return playwright.chromium.launch(executable_path=explicit, headless=True)
    if sys.platform == 'win32':
        return playwright.chromium.launch(channel='msedge', headless=True)
    chromium = Path('/usr/bin/chromium')
    if chromium.is_file():
        return playwright.chromium.launch(executable_path=str(chromium), headless=True,
                                          args=['--no-sandbox'])
    return playwright.chromium.launch(headless=True)
