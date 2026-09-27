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

echo [2/3] Building %APPNAME%.exe...
powershell -NoProfile -ExecutionPolicy Bypass -File build_flutter.ps1
if errorlevel 1 goto :fail
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APPNAME%" ^
    --add-data "MapoHwpAutoDocFitSecurity.dll;." ^
    --add-data "desktop_web;desktop_web" ^
    --collect-all tkinterdnd2 ^
    --collect-all webview ^
    --collect-all pythonnet ^
    --collect-all clr_loader ^
    hwp-auto-docfit.py
if errorlevel 1 goto :fail

echo.
echo [OK] Build succeeded.
echo Output file: dist\%APPNAME%.exe
echo You can rename it to a Korean name manually in Explorer if you want.
pause
endlocal
exit /b 0

:fail
set "BUILD_ERROR=%ERRORLEVEL%"
echo.
echo [FAIL] Build failed. Check the log above.
pause
endlocal & exit /b %BUILD_ERROR%
