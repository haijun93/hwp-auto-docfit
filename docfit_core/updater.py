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
    if expected_hash and sha256_hex.lower() != expected_hash.lower():
        return "SHA-256 검증에 실패했습니다(파일이 손상되었거나 바뀌었습니다)."
    return None


def install_script():
    """구버전을 신버전으로 교체하는 PowerShell 스크립트 본문(매개변수로 경로·PID를 받는다)."""
    return r'''param([int[]]$WaitPids, [string]$Downloaded, [string]$Target, [string]$Log)
$ErrorActionPreference = 'Stop'
function Write-Log([string]$m) { try { Add-Content -LiteralPath $Log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) -Encoding UTF8 } catch {} }
function Retry([scriptblock]$Action, [string]$What) {
    for ($i = 1; $i -le 60; $i++) {
        try { & $Action; return } catch { if ($i -eq 60) { throw "$What 실패: $($_.Exception.Message)" }; Start-Sleep -Milliseconds 500 }
    }
}
$Old = "$Target.old"
Write-Log "업데이트 시작: $Downloaded -> $Target"
foreach ($p in $WaitPids) { if ($p -gt 0) { Wait-Process -Id $p -Timeout 120 -ErrorAction SilentlyContinue } }
$replaced = $false
try {
    # 신버전 파일이 없거나 EXE가 아니면 구버전을 건드리지 않는다(교체 전에 확인).
    if (-not (Test-Path -LiteralPath $Downloaded)) { throw '내려받은 신버전 파일이 없습니다.' }
    $head = [byte[]](Get-Content -LiteralPath $Downloaded -Encoding Byte -TotalCount 2)
    if ($head.Count -lt 2 -or $head[0] -ne 0x4D -or $head[1] -ne 0x5A) { throw '내려받은 파일이 EXE가 아닙니다.' }
    if (Test-Path -LiteralPath $Old) { Retry { Remove-Item -LiteralPath $Old -Force } '이전 백업 삭제' }
    Retry { Move-Item -LiteralPath $Target -Destination $Old -Force } '구버전 이름 변경'
    $replaced = $true
    Retry { Copy-Item -LiteralPath $Downloaded -Destination $Target -Force } '신버전 복사'
    if ((Get-Item -LiteralPath $Target).Length -ne (Get-Item -LiteralPath $Downloaded).Length) { throw '복사한 파일 크기가 다릅니다.' }
    Write-Log '교체 완료, 신버전 실행'
    Start-Process -FilePath $Target
    Start-Sleep -Seconds 2
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
    if (Test-Path -LiteralPath $Target) { Start-Process -FilePath $Target }
    elseif (Test-Path -LiteralPath $Downloaded) { Start-Process -FilePath $Downloaded }
} finally {
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
