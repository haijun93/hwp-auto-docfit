"""표 서식모음 추가(table_gallery)를 다시 만들고, 한/글로 템플릿 그림을 그려 앱 내장 그림 폴더에 넣는다.

사용: python scripts/render_table_gallery.py   (한/글 2020 COM 필요, C:\\HWP_AUTODOCFIT\\.com-test.lock 잠금)
그림 이름은 표 내용 지문이라 바뀌지 않은 표의 그림은 다시 그리지 않는다.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_app.table_units_service import BUNDLED_SNAPSHOTS, GALLERY_PATH, TableUnitsService
from docfit_core.table_catalog import default_catalog_path
from docfit_core.table_gallery import build_gallery

LOCK = Path(r"C:\HWP_AUTODOCFIT\.com-test.lock")


def _factory():
    import win32com.client
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_table_catalog_paste import _register
    app = win32com.client.DispatchEx("HwpFrame.HwpObject")
    _register(app)
    return app


def main() -> int:
    build_gallery(default_catalog_path(), GALLERY_PATH)
    print("built", GALLERY_PATH)
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, b"render_table_gallery")
    os.close(fd)
    work = Path(tempfile.mkdtemp(prefix="docfit-gallery-snap-"))
    try:
        import pythoncom
        pythoncom.CoInitialize()
        service = TableUnitsService(_factory, source=default_catalog_path(), snapshot_root=work)
        result = service.thumbnails()
        made = sorted((work / "tables").glob("*.png"))
        for picture in made:
            shutil.copy2(picture, BUNDLED_SNAPSHOTS / picture.name)
        print("rendered", len(made), "ready", result["thumbnails_ready"])
    finally:
        LOCK.unlink(missing_ok=True)
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
