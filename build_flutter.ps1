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
    & $flutter pub get
    if ($LASTEXITCODE -ne 0) { throw 'Flutter dependencies failed.' }
    $webOutput = Join-Path $PSScriptRoot 'desktop_web\flutter'
    & $flutter build web --release --no-web-resources-cdn --no-wasm-dry-run "--output=$webOutput"
    if ($LASTEXITCODE -ne 0) { throw 'Flutter web build failed.' }
    Copy-Item -LiteralPath 'assets\OFL.txt' -Destination '..\desktop_web\flutter\FONT-LICENSE.txt'
} finally { Pop-Location }
