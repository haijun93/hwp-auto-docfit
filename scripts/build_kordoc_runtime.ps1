# 폐쇄망 배포용 kordoc 꾸러미(HWP_AutoDocFit_kordoc_runtime.zip)를 만든다.
# - Node.js: 고정 버전 공식 Windows ZIP을 SHA-256으로 확인한 뒤 node.exe만 담는다.
# - kordoc/OCR: 각각의 lockfile과 모델 SHA256을 확인하여 폐쇄망 실행 의존성을 포함하고,
#   설치 스크립트는 실행하지 않는다.
# 빌드 PC에만 인터넷이 필요하다. 만든 꾸러미를 EXE에 내장하여 사용 PC에서는 다운로드하지 않는다.
param(
    [string]$Output = (Join-Path $PSScriptRoot '..\release-assets\HWP_AutoDocFit_kordoc_runtime.zip')
)
$ErrorActionPreference = 'Stop'
$NodeVersion = '22.23.3'
$NodeSha256 = '2b0ff57b049cda1bbcea2240eec20467018713c1efe1f7360c2681859b90ed71'
$KordocVersion = '4.21.30'
$PandocVersion = '3.12.1'
$PandocSha256 = '6ef431cb20b2c24a0371fc19200dc49d452be54b1b5c9239f3462841ef53e587'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }
$work = Join-Path ([IO.Path]::GetTempPath()) ('docfit-kordoc-pack-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work | Out-Null
try {
    $zipName = "node-v$NodeVersion-win-x64.zip"
    $cacheDir = Join-Path $env:LOCALAPPDATA 'DocFitTools'
    $nodeZip = Join-Path $cacheDir $zipName
    if (-not (Test-Path -LiteralPath $nodeZip)) {
        New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "https://nodejs.org/dist/v$NodeVersion/$zipName" -OutFile $nodeZip
    }
    $actual = (Get-FileHash -LiteralPath $nodeZip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $NodeSha256) { throw "Node.js ZIP SHA-256 mismatch: $actual" }

    $pandocZipName = "pandoc-$PandocVersion-windows-x86_64.zip"
    $pandocZip = Join-Path $cacheDir $pandocZipName
    if (-not (Test-Path -LiteralPath $pandocZip) -or
        (Get-FileHash -LiteralPath $pandocZip -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash.ToLowerInvariant() -ne $PandocSha256) {
        New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/jgm/pandoc/releases/download/$PandocVersion/$pandocZipName" -OutFile $pandocZip
    }
    $pandocActual = (Get-FileHash -LiteralPath $pandocZip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($pandocActual -ne $PandocSha256) { throw "Pandoc ZIP SHA-256 mismatch: $pandocActual" }

    $stage = Join-Path $work 'pack'
    New-Item -ItemType Directory -Path (Join-Path $stage 'node'), (Join-Path $stage 'app'), (Join-Path $stage 'pandoc') | Out-Null
    Expand-Archive -LiteralPath $nodeZip -DestinationPath (Join-Path $work 'node-zip')
    $nodeDir = Join-Path $work "node-zip\node-v$NodeVersion-win-x64"
    Copy-Item -LiteralPath (Join-Path $nodeDir 'node.exe'), (Join-Path $nodeDir 'LICENSE') -Destination (Join-Path $stage 'node')
    Expand-Archive -LiteralPath $pandocZip -DestinationPath (Join-Path $work 'pandoc-zip')
    $pandocDir = Join-Path $work "pandoc-zip\pandoc-$PandocVersion"
    Copy-Item -LiteralPath (Join-Path $pandocDir 'pandoc.exe'), (Join-Path $pandocDir 'COPYING.rtf'), (Join-Path $pandocDir 'COPYRIGHT.txt') -Destination (Join-Path $stage 'pandoc')
    $pandoc = Join-Path $stage 'pandoc\pandoc.exe'
    $pandocObserved = (& $pandoc --version | Select-Object -First 1).Trim()
    if ($pandocObserved -notmatch [regex]::Escape($PandocVersion)) { throw "Pandoc version check failed: $pandocObserved" }
    $app = Join-Path $stage 'app'
    Copy-Item -LiteralPath (Join-Path $root 'kordoc_pack\package.json'), (Join-Path $root 'kordoc_pack\package-lock.json') -Destination $app

    $node = Join-Path $stage 'node\node.exe'
    $npm = Join-Path $nodeDir 'node_modules\npm\bin\npm-cli.js'
    Push-Location $app
    try {
        & $node $npm ci --omit=optional --ignore-scripts --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
    } finally { Pop-Location }
    # OCR dependencies are locked separately: do not install unrelated transformer/formula models.
    $ocr = Join-Path $work 'ocr'
    New-Item -ItemType Directory -Path $ocr | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'kordoc_ocr_pack\package.json'), (Join-Path $root 'kordoc_ocr_pack\package-lock.json') -Destination $ocr
    Push-Location $ocr
    try {
        & $node $npm ci --include=optional --ignore-scripts --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'OCR npm ci failed' }
    } finally { Pop-Location }
    # The npm ONNX package carries other platforms too; retain Windows x64 CPU only.
    $ortBin = Join-Path $ocr 'node_modules\onnxruntime-node\bin'
    Get-ChildItem -LiteralPath $ortBin -Recurse -File |
        Where-Object { $_.FullName -notmatch '\\win32\\x64\\' } | Remove-Item -Force
    Get-ChildItem -LiteralPath (Join-Path $ocr 'node_modules') -Force |
        Where-Object { $_.Name -ne '.package-lock.json' -and $_.Name -ne '.bin' } |
        Copy-Item -Destination (Join-Path $app 'node_modules') -Recurse -Force
    $models = Join-Path $stage 'models\ppocr'
    & $python (Join-Path $PSScriptRoot 'download_ocr_models.py') $models
    if ($LASTEXITCODE -ne 0) { throw 'OCR model checksum/download failed' }
    Copy-Item -LiteralPath (Join-Path $root 'resources\licenses\PaddleOCR-LICENSE.txt') -Destination $models
    # 실행에 필요 없는 소스 지도·형식 정의는 뺀다(라이선스 파일은 남긴다).
    # (PowerShell 5.1의 -LiteralPath와 -Include 조합은 거르지 않고 모든 파일을 넘기므로 이름으로 직접 거른다.)
    Get-ChildItem -LiteralPath (Join-Path $app 'node_modules') -Recurse -File |
        Where-Object { $_.Name -match '\.(map|d\.ts|d\.mts|d\.cts)$' } |
        Remove-Item -Force

    $cli = Join-Path $app 'node_modules\kordoc\dist\cli.js'
    $observed = (& $node $cli --version | Out-String).Trim()
    if ($observed -notmatch [regex]::Escape($KordocVersion)) { throw "kordoc version check failed: $observed" }

    $manifest = [ordered]@{ kordoc = $KordocVersion; node = $NodeVersion; node_sha256 = $NodeSha256; bundle_revision = 'ocr-pandoc-1'; ocr = 'ppocr-korean-v5'; pandoc = $PandocVersion; pandoc_sha256 = $PandocSha256; pandoc_license = 'GPL-2.0-or-later' } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $stage 'runtime.json'), $manifest, (New-Object Text.UTF8Encoding($false)))

    & $python (Join-Path $PSScriptRoot 'verify_runtime_ocr.py') $stage
    if ($LASTEXITCODE -ne 0) { throw 'Packaged offline OCR functional test failed' }
    & $python (Join-Path $PSScriptRoot 'verify_runtime_pandoc.py') $stage
    if ($LASTEXITCODE -ne 0) { throw 'Packaged offline Pandoc HTML/DOCX/EPUB functional test failed' }

    $outputPath = [IO.Path]::GetFullPath($Output)
    New-Item -ItemType Directory -Force -Path (Split-Path $outputPath) | Out-Null
    if (Test-Path -LiteralPath $outputPath) { Remove-Item -LiteralPath $outputPath -Force }
    # PowerShell 5.1 Compress-Archive는 경로 구분자를 '\'로 기록하므로 Python zipfile로 묶는다.
    & $python (Join-Path $PSScriptRoot 'zip_folder.py') $stage $outputPath
    if ($LASTEXITCODE -ne 0) { throw 'runtime ZIP creation failed' }
    $hash = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText("$outputPath.sha256", "$hash  $(Split-Path $outputPath -Leaf)`n", (New-Object Text.UTF8Encoding($false)))
    $size = [math]::Round((Get-Item -LiteralPath $outputPath).Length / 1MB, 1)
    Write-Host "kordoc runtime pack: $outputPath ($size MB, kordoc $observed, node $NodeVersion, $pandocObserved, sha256 $hash)"
} finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
