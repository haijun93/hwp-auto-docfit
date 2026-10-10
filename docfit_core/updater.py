"""자동 업데이트의 검증·교체 로직(한/글·화면 없이 시험할 수 있는 부분).

설계(2026-10-09):
1. 내려받기는 '.part'로 받고 크기·EXE 머리(MZ)·SHA-256(자산 digest 또는 릴리스 노트의 SHA-256)을 확인한 뒤 확정한다.
2. 교체는 별도 PowerShell 스크립트가 앱(그리고 PyInstaller 부트로더) 프로세스가 끝나기를 기다린 뒤
   구버전을 '.old'로 이름 바꾸고(실행 중인 EXE도 이름 변경은 된다) 새 파일을 원래 이름으로 넣은 다음 새 버전을 실행한다.
   어느 단계든 실패하면 '.old'를 되살려 구버전을 다시 실행한다. 각 단계는 잠금(백신 검사 등)에 대비해 재시도한다.
3. 다음 실행 때 남은 '.old'와 내려받기 잔여물을 지운다.
"""
import re

SHA256_PATTERN = re.compile(r"SHA-?256[^0-9A-Fa-f]{0,20}([0-9A-Fa-f]{64})")


def expected_sha256(release, asset):
    """자산 digest('sha256:…') 또는 릴리스 설명(GitLab description·GitHub body)에서 SHA-256을 찾는다(소문자, 없으면 None)."""
    digest = str((asset or {}).get("digest") or "")
    if digest.lower().startswith("sha256:") and len(digest) == 71:
        return digest[7:].lower()
    for key in ("description", "body"):
        match = SHA256_PATTERN.search(str((release or {}).get(key) or ""))
        if match:
            return match.group(1).lower()
    return None


def verify_download(size, head, sha256_hex, expected_size=None, expected_hash=None):
    """내려받은 파일 검증. 문제가 있으면 사람이 읽을 수 있는 이유를, 괜찮으면 None을 돌려준다."""
    if size <= 0:
        return "내려받은 파일이 비어 있습니다."
    if expected_size and size != int(expected_size):
        return f"파일 크기가 다릅니다(받은 {size:,}바이트, 예상 {int(expected_size):,}바이트)."
    if not bytes(head or b"").startswith(b"MZ"):
        return "실행 파일(EXE)이 아닙니다. 네트워크 오류 페이지를 받았을 수 있습니다."
    # 보안(2026-10-09 검토): SHA-256을 확인할 수 없으면 설치하지 않는다(실패 시 닫힘).
    if not expected_hash:
        return "릴리스에 SHA-256 정보가 없어 안전을 위해 자동 업데이트를 중단했습니다."
    if sha256_hex.lower() != expected_hash.lower():
        return "SHA-256 검증에 실패했습니다(파일이 손상되었거나 바뀌었습니다)."
    return None


def launch_environment(environ):
    """업데이트 스크립트에 넘길 환경 변수: PyInstaller 단일 실행 파일의 내부 변수(_PYI_*, _MEIPASS2)를 뺀다.

    구버전이 넘긴 이 변수가 남으면 같은 경로에 들어간 새 exe가 자신을 구버전의 자식 프로세스로 알고 이미 지워진
    구버전 임시 폴더(_MEI…)에서 python312.dll을 찾다가 'Failed to load Python DLL'로 멈췄다(2026-10-10 사용자
    업데이트 오류). PYINSTALLER_RESET_ENVIRONMENT=1은 새 exe가 언제나 새로 시작하게 한다.
    """
    env = {k: v for k, v in dict(environ).items()
           if not k.upper().startswith("_PYI_") and k.upper() != "_MEIPASS2"}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def install_script():
    """구버전을 신버전으로 교체하는 PowerShell 스크립트 본문(매개변수로 경로·PID를 받는다)."""
    return r'''param([string]$WaitPidList, [string]$Downloaded, [string]$Target, [string]$Log, [string]$Sha256,
      [string]$StartedFlag, [string]$BusyFlag)
$ErrorActionPreference = 'Stop'
function Write-Log([string]$m) { try { Add-Content -LiteralPath $Log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) -Encoding UTF8 } catch {} }
function Retry([scriptblock]$Action, [string]$What) {
    for ($i = 1; $i -le 60; $i++) {
        try { & $Action; return } catch { if ($i -eq 60) { throw "$What 실패: $($_.Exception.Message)" }; Start-Sleep -Milliseconds 500 }
    }
}
$Old = "$Target.old"
# PyInstaller 단일 실행 파일의 내부 변수를 지운다. 남아 있으면 새로 실행한 exe가 이미 지워진 구버전 임시 폴더에서
# python312.dll을 찾다가 'Failed to load Python DLL'로 멈춘다(2026-10-10 업데이트 오류).
Get-ChildItem Env: | Where-Object { $_.Name -like '_PYI_*' -or $_.Name -eq '_MEIPASS2' } | ForEach-Object { Remove-Item -LiteralPath ("Env:" + $_.Name) -ErrorAction SilentlyContinue }
$env:PYINSTALLER_RESET_ENVIRONMENT = '1'
Write-Log "업데이트 시작: $Downloaded -> $Target"
if ($BusyFlag) { try { Set-Content -LiteralPath $BusyFlag -Value $PID -Encoding UTF8 } catch {} }
# PID 목록은 글자 하나로 받아 직접 나눈다(-File로 넘긴 '1,2'는 [int[]]가 아니라 숫자 12로 묶였다. Beta 12 리뷰 R1).
$WaitPids = @()
foreach ($t in ($WaitPidList -split '[^0-9]+')) { if ($t) { $WaitPids += [int]$t } }
Write-Log ("대기 PID: " + ($WaitPids -join ', '))
foreach ($p in $WaitPids) { if ($p -gt 0) { Wait-Process -Id $p -Timeout 120 -ErrorAction SilentlyContinue } }
$stillRunning = @($WaitPids | Where-Object { $_ -gt 0 -and (Get-Process -Id $_ -ErrorAction SilentlyContinue) })
$replaced = $false
try {
    if ($stillRunning.Count -gt 0) { throw ("앱이 아직 실행 중입니다(PID " + ($stillRunning -join ', ') + "). 교체하지 않습니다.") }
    # 신버전 파일이 없거나 EXE가 아니면 구버전을 건드리지 않는다(교체 전에 확인).
    if (-not (Test-Path -LiteralPath $Downloaded)) { throw '내려받은 신버전 파일이 없습니다.' }
    $head = [byte[]](Get-Content -LiteralPath $Downloaded -Encoding Byte -TotalCount 2)
    if ($head.Count -lt 2 -or $head[0] -ne 0x4D -or $head[1] -ne 0x5A) { throw '내려받은 파일이 EXE가 아닙니다.' }
    # 앱이 검증한 뒤 교체하기 전에 파일이 바뀌지 않았는지 다시 확인한다(검증-사용 사이 바꿔치기 방지).
    if (-not $Sha256 -or (Get-FileHash -LiteralPath $Downloaded -Algorithm SHA256).Hash -ne $Sha256.ToUpper()) { throw '내려받은 파일의 SHA-256이 검증 때와 다릅니다.' }
    if (Test-Path -LiteralPath $Old) { Retry { Remove-Item -LiteralPath $Old -Force } '이전 백업 삭제' }
    Retry { Move-Item -LiteralPath $Target -Destination $Old -Force } '구버전 이름 변경'
    $replaced = $true
    Retry { Copy-Item -LiteralPath $Downloaded -Destination $Target -Force } '신버전 복사'
    if ((Get-Item -LiteralPath $Target).Length -ne (Get-Item -LiteralPath $Downloaded).Length) { throw '복사한 파일 크기가 다릅니다.' }
    Write-Log '교체 완료, 신버전 실행'
    if ($StartedFlag -and (Test-Path -LiteralPath $StartedFlag)) { Remove-Item -LiteralPath $StartedFlag -Force -ErrorAction SilentlyContinue }
    $newProc = Start-Process -FilePath $Target -PassThru
    # 새 버전이 실제로 켜졌는지(시작 확인 파일) 확인한 뒤에만 구버전 백업을 지운다(Beta 12 리뷰 R5).
    if ($StartedFlag) {
        $ok = $false
        for ($i = 0; $i -lt 120; $i++) { if (Test-Path -LiteralPath $StartedFlag) { $ok = $true; break }; Start-Sleep -Milliseconds 500 }
        if (-not $ok) {
            Write-Log '신버전 시작 확인 실패(60초): 신버전을 끄고 구버전으로 되돌립니다.'
            try { if ($newProc) { Stop-Process -Id $newProc.Id -Force -ErrorAction SilentlyContinue }; Get-Process | Where-Object { $_.Path -eq $Target } | Stop-Process -Force -ErrorAction SilentlyContinue } catch {}
            Start-Sleep -Seconds 2
            throw '신버전이 정상적으로 시작되지 않았습니다.'
        }
        Write-Log '신버전 시작 확인'
    } else { Start-Sleep -Seconds 2 }
    try { Remove-Item -LiteralPath $Downloaded -Force } catch { Write-Log "내려받은 파일은 다음 실행 때 정리: $($_.Exception.Message)" }
    try { Remove-Item -LiteralPath $Old -Force } catch { Write-Log "구버전 백업은 다음 실행 때 정리: $($_.Exception.Message)" }
} catch {
    Write-Log "교체 실패: $($_.Exception.Message)"
    if ($replaced) {
        try {
            if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Force }
            Move-Item -LiteralPath $Old -Destination $Target -Force
            Write-Log '구버전 복구, 구버전 실행'
        } catch { Write-Log "구버전 복구 실패: $($_.Exception.Message)" }
    }
    # 검증에 실패했을 수 있는 내려받은 파일은 실행하지 않는다. 구버전만 다시 실행한다(앱이 아직 돌고 있으면 하지 않음).
    if ($stillRunning.Count -eq 0 -and (Test-Path -LiteralPath $Target)) { Start-Process -FilePath $Target }
} finally {
    if ($BusyFlag) { Remove-Item -LiteralPath $BusyFlag -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
}
'''


def leftover_files(exe_dir_names, update_dir_names, keep=()):
    """정리할 파일 이름 목록: 실행 폴더의 '*.exe.old', 업데이트 폴더의 '*.part'·지난 내려받기('HWP_AutoDocFit-*.exe')·남은 스크립트."""
    old = [n for n in exe_dir_names if n.lower().endswith(".exe.old")]
    stale = [n for n in update_dir_names
             if n not in keep and (n.lower().endswith(".part") or n.lower().endswith(".ps1")
                                   or (n.lower().startswith("hwp_autodocfit-") and n.lower().endswith(".exe")))]
    return old, stale
