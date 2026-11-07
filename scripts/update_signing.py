"""latest.json Ed25519 키 생성·서명 도구 (SEC1/S1).

비밀키는 저장소 밖 파일(--key-file) 또는 환경변수 DOCFIT_UPDATE_SIGNING_KEY(base64 32바이트)로만 받는다.
저장소 안 경로는 거부한다.

  python scripts/update_signing.py keygen --key-file ~/secure/update.key   # 공개키(base64)를 출력
  python scripts/update_signing.py sign latest.json [--key-file ...]       # signature 필드를 기록
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from docfit_core.update_signature import canonical_bytes  # noqa: E402

ENV = "DOCFIT_UPDATE_SIGNING_KEY"
RAW = dict(encoding=serialization.Encoding.Raw)


def _outside_repo(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise SystemExit("비밀키 경로가 저장소 안입니다. 저장소 밖 경로를 지정하세요.")
    return path


def public_b64(private: Ed25519PrivateKey) -> str:
    raw = private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode("ascii")


def private_raw(private: Ed25519PrivateKey) -> bytes:
    return private.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw,
                                 encryption_algorithm=serialization.NoEncryption())


def load_private(key_file=None, environ=None) -> Ed25519PrivateKey:
    environ = os.environ if environ is None else environ
    if key_file:
        text = _outside_repo(Path(key_file)).read_text(encoding="ascii").strip()
    elif environ.get(ENV):
        text = environ[ENV].strip()
    else:
        raise SystemExit(f"비밀키가 없습니다. --key-file 또는 환경변수 {ENV}를 지정하세요.")
    try:
        return Ed25519PrivateKey.from_private_bytes(base64.b64decode(text, validate=True))
    except Exception:
        raise SystemExit("비밀키 형식이 올바르지 않습니다(base64 32바이트).") from None


def keygen(key_file: Path) -> str:
    path = _outside_repo(key_file)
    if path.exists():
        raise SystemExit("이미 있는 파일은 덮어쓰지 않습니다.")
    private = Ed25519PrivateKey.generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(base64.b64encode(private_raw(private)).decode("ascii") + "\n")
    return public_b64(private)


def sign_file(latest: Path, private: Ed25519PrivateKey) -> None:
    data = json.loads(latest.read_text(encoding="utf-8-sig"))
    data.pop("signature", None)
    data["signature"] = base64.b64encode(private.sign(canonical_bytes(data))).decode("ascii")
    latest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("keygen")
    gen.add_argument("--key-file", required=True)
    sig = sub.add_parser("sign")
    sig.add_argument("latest")
    sig.add_argument("--key-file")
    args = parser.parse_args(argv)
    if args.cmd == "keygen":
        print(keygen(Path(args.key_file)))
    else:
        sign_file(Path(args.latest), load_private(args.key_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
