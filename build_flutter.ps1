param([string]$FlutterSdk = $env:FLUTTER_SDK)
$ErrorActionPreference = 'Stop'
$flutter = if ($FlutterSdk) { Join-Path $FlutterSdk 'bin\flutter.bat' } else { 'flutter' }
if (-not (Get-Command $flutter -ErrorAction SilentlyContinue)) {
    $localSdk = Join-Path $env:LOCALAPPDATA 'DocFitTools\flutter\bin\flutter.bat'
    if (Test-Path -LiteralPath $localSdk) { $flutter = $localSdk }
    else { throw 'Flutter SDK not found. Set FLUTTER_SDK or add flutter to PATH.' }
}
Push-Location (Join-Path $PSScriptRoot 'flutter_ui')
try {
    & $flutter pub get --enforce-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Flutter dependencies failed.' }
    # Run the same SDK's analyzer directly. Flutter's LSP wrapper can truncate
    # JSON messages on Windows paths; do not weaken or skip analysis on failure.
    $dart = Join-Path (Split-Path (Get-Command $flutter).Source -Parent) 'dart.bat'
    & $dart analyze --fatal-infos
    if ($LASTEXITCODE -ne 0) { throw 'Flutter analysis failed.' }
    & $flutter test --no-pub
    if ($LASTEXITCODE -ne 0) { throw 'Flutter tests failed.' }
    $webOutput = Join-Path $PSScriptRoot 'desktop_web\flutter'
    & $flutter build web --release --no-pub --no-web-resources-cdn --no-wasm-dry-run "--output=$webOutput"
    if ($LASTEXITCODE -ne 0) { throw 'Flutter web build failed.' }
    Copy-Item -LiteralPath 'assets\OFL.txt' -Destination '..\desktop_web\flutter\FONT-LICENSE.txt'
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }
    & $python (Join-Path $PSScriptRoot 'scripts\verify_flutter_bundle.py') $webOutput
    if ($LASTEXITCODE -ne 0) { throw 'Flutter bundle verification failed.' }
} finally { Pop-Location }
