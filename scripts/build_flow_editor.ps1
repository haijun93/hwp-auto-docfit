param([string]$Npm = 'npm')
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
if ([version]((& node --version).TrimStart('v')) -lt [version]'22.12.0') {
    throw 'Flow editor build requires Node.js 22.12.0 or newer.'
}
Push-Location (Join-Path $Root 'diagram_editor')
try {
    & $Npm ci --ignore-scripts --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor dependencies failed.' }
    & $Npm test
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor tests failed.' }
    & $Npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor build failed.' }
} finally { Pop-Location }
