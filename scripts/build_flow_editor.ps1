param([string]$Npm = 'npm')
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
function Invoke-BuildNpm([string[]]$Arguments) {
    # Windows PowerShell 5.1 turns npm's harmless stderr notices into errors
    # under Stop. The process exit code remains the authoritative build gate.
    $ErrorActionPreference = 'Continue'
    & $Npm @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Flow editor npm failed (exit $LASTEXITCODE)." }
}
if ([version]((& node --version).TrimStart('v')) -lt [version]'22.12.0') {
    throw 'Flow editor build requires Node.js 22.12.0 or newer.'
}
Push-Location (Join-Path $Root 'diagram_editor')
try {
    Invoke-BuildNpm -Arguments @('ci', '--ignore-scripts', '--no-audit', '--no-fund')
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor dependencies failed.' }
    Invoke-BuildNpm -Arguments @('test')
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor tests failed.' }
    Invoke-BuildNpm -Arguments @('run', 'build')
    if ($LASTEXITCODE -ne 0) { throw 'Flow editor build failed.' }
} finally { Pop-Location }
