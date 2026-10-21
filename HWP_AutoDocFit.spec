# Single packaging definition shared by build.bat and Windows CI.
from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path
root = Path(SPECPATH)
datas = [(str(root / 'MapoHwpAutoDocFitSecurity.dll'), '.'),
         (str(root / 'desktop_web'), 'desktop_web'),
         (str(root / 'resources'), 'resources')]
pack = root / 'resources' / 'HWP_AutoDocFit_kordoc_runtime.zip'
if not pack.is_file() or not pack.with_name(pack.name + '.sha256').is_file():
    raise RuntimeError('Build the embedded offline runtime before PyInstaller packaging')
binaries, hiddenimports = [], []
for package in ('docfit_core', 'docfit_engine', 'docfit_app', 'docfit_ui'):
    hiddenimports += collect_submodules(package)
for package in ('tkinterdnd2', 'PIL', 'webview', 'pythonnet', 'clr_loader', 'pypdfium2', 'pypdfium2_raw', 'pypdf', 'cryptography'):
    data, binary, imports = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += imports
a = Analysis([str(root / 'hwp-auto-docfit.py')], pathex=[str(root)],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports)
pyz = PYZ(a.pure)
installer_exe = EXE(pyz, a.scripts, [], name='HWP_AutoDocFit',
                     console=False, icon=str(root / 'resources' / 'app_icon.ico'),
                     exclude_binaries=True)
installer_bundle = COLLECT(installer_exe, a.binaries, a.datas, name='HWP_AutoDocFit')
