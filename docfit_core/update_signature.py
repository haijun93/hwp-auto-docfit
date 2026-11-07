"""latest.json Ed25519 서명 검증 (SEC1/S1).

서명 대상: 최상위 "signature" 키를 뺀 나머지 JSON을 정규화한 바이트
(sort_keys, 구분자 (",", ":"), ensure_ascii=True, UTF-8).
서명 형식: "signature" 키에 Ed25519 서명 64바이트의 base64.
공개키: 32바이트 원시 값의 base64. 비밀키는 이 저장소에 두지 않는다.
"""
from __future__ import annotations

import base64
import binascii
import json
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# 기능 플래그: 기본 꺼짐. 켜려면 환경변수 DOCFIT_VERIFY_UPDATE_SIGNATURE=1 (또는 아래 상수를 True로).
VERIFY_UPDATE_SIGNATURE = False
# 사용자 결정 필요: 실제 공개키(base64 32바이트)는 키 생성 후 여기에 넣는다. 비어 있으면 검증 켠 상태에서 업데이트 거부.
UPDATE_PUBLIC_KEY_B64 = ""


class SignatureError(Exception):
    pass


def enabled(environ=None) -> bool:
    env = (environ if environ is not None else os.environ).get("DOCFIT_VERIFY_UPDATE_SIGNATURE")
    if env is not None:
        return env.strip().lower() in ("1", "true", "yes", "on")
    return bool(VERIFY_UPDATE_SIGNATURE)


def canonical_bytes(data: dict) -> bytes:
    body = {k: v for k, v in data.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _b64(value: str, what: str, length: int) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError, TypeError):
        raise SignatureError(f"{what} 형식이 올바르지 않습니다.") from None
    if len(raw) != length:
        raise SignatureError(f"{what} 길이가 올바르지 않습니다.")
    return raw


def verify_latest(data, public_key_b64: str | None = None) -> None:
    """서명이 올바르지 않으면 SignatureError. 통과하면 None."""
    key_b64 = UPDATE_PUBLIC_KEY_B64 if public_key_b64 is None else public_key_b64
    if not key_b64:
        raise SignatureError("앱에 업데이트 서명 공개키가 설정되어 있지 않아 업데이트를 거부합니다.")
    if not isinstance(data, dict):
        raise SignatureError("업데이트 정보 형식이 올바르지 않습니다.")
    signature = data.get("signature")
    if not isinstance(signature, str) or not signature:
        raise SignatureError("업데이트 정보에 서명이 없어 업데이트를 거부합니다.")
    key = Ed25519PublicKey.from_public_bytes(_b64(key_b64, "공개키", 32))
    try:
        key.verify(_b64(signature, "서명", 64), canonical_bytes(data))
    except InvalidSignature:
        raise SignatureError("업데이트 정보 서명이 일치하지 않아 업데이트를 거부합니다.") from None
