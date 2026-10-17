param([string]$Npm = 'npm')
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
function Invoke-BuildNpm([string[]]$Arguments) {
    $ErrorActionPreference = 'Continue'
    & $Npm @Arguments
    if ($LASTEXITCODE -ne 0) { throw "HWP preview npm failed (exit $LASTEXITCODE)." }
}
if ([version]((& node --version).TrimStart('v')) -lt [version]'22.12.0') {
    throw 'HWP typeset preview build requires Node.js 22.12.0 or newer.'
}
Push-Location (Join-Path $Root 'hwp_preview')
try {
    Invoke-BuildNpm -Arguments @('ci', '--ignore-scripts', '--no-audit', '--no-fund')
    if ($LASTEXITCODE -ne 0) { throw 'HWP typeset preview dependencies failed.' }
    Invoke-BuildNpm -Arguments @('test')
    if ($LASTEXITCODE -ne 0) { throw 'HWP typeset preview tests failed.' }
    Invoke-BuildNpm -Arguments @('run', 'build')
    if ($LASTEXITCODE -ne 0) { throw 'HWP typeset preview build failed.' }
} finally { Pop-Location }
