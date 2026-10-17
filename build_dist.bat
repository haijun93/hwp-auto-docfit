@echo off
setlocal EnableExtensions
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo [FAIL] .venv\Scripts\python.exe not found. Run build.bat once to prepare dependencies.
  exit /b 1
)

for /f %%V in ('%PYTHON% scripts\read_app_version.py') do set "VERSION=%%V"
if not defined VERSION (
  echo [FAIL] Could not read APP_VERSION.
  exit /b 1
)
set "ISCC="
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

echo [1/6] Building Flutter assets...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_flutter.ps1"
if errorlevel 1 goto :fail

echo [2/6] Preparing embedded offline runtime...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_kordoc_runtime.ps1" -Output "%~dp0resources\HWP_AutoDocFit_kordoc_runtime.zip"
if errorlevel 1 goto :fail

echo [3/6] Building portable Onefile and installer Onedir from one analysis...
"%PYTHON%" -m PyInstaller --noconfirm --clean "HWP_AutoDocFit.spec"
if errorlevel 1 goto :fail
copy /y "dist\HWP_AutoDocFit.exe" "dist\HWP_AutoDocFit_v%VERSION%_Portable.exe" >nul
if errorlevel 1 goto :fail

if not defined ISCC (
  echo [4/6] Inno Setup ISCC.exe not found; portable build completed, installer skipped.
  echo Install Inno Setup 6 to also build the Setup.exe distribution.
  exit /b 0
)

echo [5/6] Building per-user installer...
set "DOCFIT_VERSION=%VERSION%"
"%ISCC%" /Qp "installer\setup.iss"
if errorlevel 1 goto :fail

echo [6/6] Verifying output files...
if not exist "dist\HWP_AutoDocFit_v%VERSION%_Portable.exe" goto :missing
if not exist "dist\HWP_AutoDocFit_v%VERSION%_Setup.exe" goto :missing
echo [OK] dist\HWP_AutoDocFit_v%VERSION%_Portable.exe
echo [OK] dist\HWP_AutoDocFit_v%VERSION%_Setup.exe
exit /b 0

:missing
echo [FAIL] Expected build output is missing.
exit /b 1

:fail
set "BUILD_ERROR=%ERRORLEVEL%"
echo [FAIL] Build failed with exit code %BUILD_ERROR%.
exit /b %BUILD_ERROR%
