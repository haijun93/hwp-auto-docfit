@echo off
setlocal

cd /d "%~dp0"

set "APPNAME=HWP_AutoDocFit"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [FAIL] Virtual environment Python was not found: %PYTHON%
    echo Run: python -m venv .venv
    pause
    exit /b 1
)

echo [1/3] Installing build dependencies...
"%PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [2/3] Checking Pillow image support...
"%PYTHON%" -c "from PIL import Image, ImageTk, ImageOps; print('Pillow', Image.__version__)"
if errorlevel 1 goto :fail

echo [3/3] Building %APPNAME%.exe...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APPNAME%" ^
    --add-data "MapoHwpAutoDocFitSecurity.dll;." ^
    --collect-all tkinterdnd2 ^
    --collect-all PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL.ImageOps ^
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
