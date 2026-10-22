"""GitLab `downloads` 브랜치에 배포 파일을 올린다(공공기관 PC는 GitHub가 막혀 있음, 2026-10-22 사용자 요청).

사용: .venv\\Scripts\\python.exe scripts\\publish_gitlab_downloads.py 1.80.3

GitHub 릴리스에서 포터블·설치용 exe와 SHA256SUMS를 받아 해시를 확인하고, 시험용 예시 TXT와 함께
부모 없는 커밋 하나로 만든 뒤 GitLab(origin)의 `downloads` 브랜치에 강제로 올린다. 브랜치는 늘 최신 버전 하나만
가지므로 옛 exe가 저장소 용량에 쌓이지 않는다(main·alpha·태그와 무관한 별도 기록, GitHub에는 올리지 않음).
README의 다운로드 링크는 `-/raw/downloads/<파일>?inline=false` 형식이다.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/haijun93/hwp-auto-docfit/releases/download/v{version}/{name}"
GITLAB = "https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit.git"
EXAMPLE = ROOT / "release-assets" / "보고서 예시 파일(한번에 적용).txt"


def _git(work: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=work, check=True)


def main(version: str) -> int:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit("버전은 1.80.4처럼 숫자 세 개로 주세요.")
    names =[f"HWP_AutoDocFit_v{version}_Portable.exe", f"HWP_AutoDocFit_v{version}_Setup.exe", "SHA256SUMS"]
    work = Path(tempfile.mkdtemp(prefix="docfit_gitlab_downloads_"))
    try:
        for name in names:
            # GitLab 보안 검사(Semgrep)가 urllib의 동적 주소를 막으므로 Windows 기본 curl로 https만 받는다.
            subprocess.run(["curl", "--fail", "--location", "--proto", "=https", "--silent", "--show-error",
                            "--max-time", "900", "--output", str(work / name),
                            GITHUB.format(version=version, name=name)], check=True)
        expected = {}
        for line in (work / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, _, path = line.partition(" ")
            expected[Path(path.lstrip("*")).name] = digest.lower()
        for name in names[:2]:
            actual = hashlib.sha256((work / name).read_bytes()).hexdigest()
            if expected.get(name) != actual:
                raise SystemExit(f"SHA-256 불일치: {name}")
        shutil.copyfile(EXAMPLE, work / EXAMPLE.name)
        (work / "README.md").write_text(
            f"# 한글편집 후처리 v{version} 내려받기 (GitLab)\n\n"
            "공공기관 PC에서 GitHub가 막혀 있어 배포 파일을 이 브랜치에 둡니다. 소스는 main 브랜치를 보세요.\n\n"
            f"- {names[0]} — 설치 없이 바로 실행\n- {names[1]} — 설치용\n"
            f"- {EXAMPLE.name} — 처음 체험용 예시\n- SHA256SUMS — 내려받은 파일 확인용 해시\n",
            encoding="utf-8")
        _git(work, "init", "-q", "-b", "downloads")
        _git(work, "add", "-A")
        _git(work, "-c", "user.name=마포구청 공혁준", "-c", "user.email=mapo4good@mapo.go.kr",
             "commit", "-q", "-m", f"v{version} 배포 파일(GitLab 내려받기 전용 브랜치)")
        _git(work, "-c", "http.postBuffer=1048576000", "push", "--force", GITLAB, "downloads:refs/heads/downloads")
        print(f"GitLab downloads 브랜치에 v{version} 배포 파일을 올렸습니다.")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("사용: publish_gitlab_downloads.py <버전>")
    raise SystemExit(main(sys.argv[1]))
