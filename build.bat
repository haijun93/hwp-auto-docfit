@echo off
setlocal

cd /d "%~dp0"

set "APPNAME=HWP_AutoDocFit"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [0/4] Virtual environment not found. Creating .venv ...
    set "BASEPY="
    py -3 --version >nul 2>&1 && set "BASEPY=py -3"
    if not defined BASEPY (
        python --version >nul 2>&1 && set "BASEPY=python"
    )
    if not defined BASEPY (
        echo [FAIL] Python was not found on this PC.
        echo Install Python 3.11 or later from https://www.python.org/downloads/
        echo and make sure to check "Add python.exe to PATH" during installation.
        pause
        exit /b 1
    )
    %BASEPY% -m venv .venv
    if errorlevel 1 goto :fail
)

if not exist "%PYTHON%" (
    echo [FAIL] Virtual environment Python still not found: %PYTHON%
    pause
    exit /b 1
)

echo [1/4] Installing build dependencies...
"%PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [2/4] Building Flutter interface...
powershell -NoProfile -ExecutionPolicy Bypass -File build_flutter.ps1
if errorlevel 1 (
    echo.
    echo [WARN] Flutter UI was not built ^(Flutter SDK missing or build error^).
    echo [WARN] Continuing without it: the app will use the built-in WebView/Tk screen.
    echo.
)

echo [3/4] Building %APPNAME%.exe...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APPNAME%" ^
    --add-data "MapoHwpAutoDocFitSecurity.dll;." ^
    --add-data "desktop_web;desktop_web" ^
    --add-data "resources;resources" ^
    --collect-all tkinterdnd2 ^
    --collect-all webview ^
    --collect-all pythonnet ^
    --collect-all clr_loader ^
    --collect-all pypdfium2 ^
    --collect-all pypdfium2_raw ^
    hwp-auto-docfit.py
if errorlevel 1 goto :fail

echo [4/4] Building 설치파일 초기화.exe (Cleanup ^& Reset Tool)...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "HWP_AutoDocFit_Reset" ^
    hwp-auto-docfit-reset.py
if errorlevel 1 goto :fail
"%PYTHON%" -c "import shutil; shutil.move('dist/HWP_AutoDocFit_Reset.exe', 'dist/설치파일 초기화.exe')"

echo.
echo [OK] Build succeeded.
echo Output files:
echo   - dist\%APPNAME%.exe (Main App)
echo   - dist\설치파일 초기화.exe (Reset Tool)
pause
endlocal
exit /b 0

:fail
set "BUILD_ERROR=%ERRORLEVEL%"
echo.
echo [FAIL] Build failed. Check the log above.
pause
endlocal & exit /b %BUILD_ERROR%
