"""Ed25519 서명 기반 업데이트 메타데이터 무결성 검증 모듈 (S1)."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import re
from typing import Mapping

DEFAULT_TRUSTED_KEYS: Mapping[str, bytes] = {}
REQUIRE_SIGNED_UPDATES = False


class UpdateTrustError(ValueError):
    """업데이트 서명 또는 메타데이터 무결성 검증 실패."""
    pass


@dataclass(frozen=True)
class UpdateTrustPolicy:
    require_signed: bool
    public_keys: Mapping[str, bytes]  # key_id -> 32-byte raw public key


def default_update_trust_policy() -> UpdateTrustPolicy:
    return UpdateTrustPolicy(
        require_signed=REQUIRE_SIGNED_UPDATES,
        public_keys=dict(DEFAULT_TRUSTED_KEYS),
    )


def verify_signed_manifest(envelope_bytes: bytes, *, policy: UpdateTrustPolicy,
                           now: datetime | None = None) -> dict:
    if len(envelope_bytes) > 256 * 1024:
        raise UpdateTrustError("업데이트 메타데이터 봉투 크기가 256KiB를 초과합니다.")
    try:
        envelope = json.loads(envelope_bytes.decode("utf-8"))
    except Exception as exc:
        raise UpdateTrustError("업데이트 봉투 JSON 디코딩 실패") from exc

    if not isinstance(envelope, dict):
        raise UpdateTrustError("올바르지 않은 업데이트 봉투 형식입니다.")

    for field in ("schema", "key_id", "payload", "signature"):
        if field not in envelope or not isinstance(envelope[field], (str if field != "schema" else int)):
            raise UpdateTrustError(f"봉투 필수 필드 누락 또는 형식 불일치: {field}")

    if envelope["schema"] != 1:
        raise UpdateTrustError(f"지원하지 않는 봉투 스키마 버전: {envelope['schema']}")

    key_id = envelope["key_id"]
    if key_id not in policy.public_keys:
        raise UpdateTrustError(f"신뢰할 수 없는 key_id: {key_id}")

    raw_public_key = policy.public_keys[key_id]
    if len(raw_public_key) != 32:
        raise UpdateTrustError("잘못된 공개키 길이입니다.")

    try:
        signature = base64.b64decode(envelope["signature"], validate=True)
        payload_bytes = base64.b64decode(envelope["payload"], validate=True)
    except Exception as exc:
        raise UpdateTrustError("Base64 디코딩 실패") from exc

    if len(signature) != 64:
        raise UpdateTrustError("서명 바이트 길이가 64바이트가 아닙니다.")

    if len(payload_bytes) > 128 * 1024:
        raise UpdateTrustError("페이로드 크기가 128KiB를 초과합니다.")

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature

    signed_data = b"HWP-AutoDocFit/update/v1\x00" + payload_bytes
    try:
        pubkey = Ed25519PublicKey.from_public_bytes(raw_public_key)
        pubkey.verify(signature, signed_data)
    except InvalidSignature as exc:
        raise UpdateTrustError("Ed25519 서명 검증 실패") from exc
    except Exception as exc:
        raise UpdateTrustError(f"서명 검증 중 오류: {exc}") from exc

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise UpdateTrustError("페이로드 JSON 디코딩 실패") from exc

    if not isinstance(payload, dict):
        raise UpdateTrustError("페이로드는 JSON 객체여야 합니다.")

    if payload.get("product") != "HWP_AutoDocFit":
        raise UpdateTrustError("대상 제품이 일치하지 않습니다.")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    try:
        issued_at = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    except Exception as exc:
        raise UpdateTrustError("날짜 형식(RFC3339) 파싱 실패") from exc

    if issued_at > expires_at:
        raise UpdateTrustError("발행 시각이 만료 시각보다 늦습니다.")

    if issued_at > current_time + timedelta(minutes=5):
        raise UpdateTrustError("미래에 발행된 메타데이터입니다.")

    if current_time >= expires_at:
        raise UpdateTrustError("만료된 업데이트 메타데이터입니다.")

    if (expires_at - issued_at).total_seconds() > 30 * 86400:
        raise UpdateTrustError("유효기간이 30일을 초과합니다.")

    if "version" not in payload or not isinstance(payload["version"], str):
        raise UpdateTrustError("version 필드가 올바르지 않습니다.")
    if "files" not in payload or not isinstance(payload["files"], dict):
        raise UpdateTrustError("files 필드가 올바르지 않습니다.")

    for kind in ("portable", "setup"):
        item = payload["files"].get(kind)
        if not isinstance(item, dict):
            raise UpdateTrustError(f"files.{kind} 정보가 올바르지 않습니다.")
        for k in ("name", "size", "sha256", "urls"):
            if k not in item:
                raise UpdateTrustError(f"files.{kind}.{k} 누락")
        if not isinstance(item["size"], int) or isinstance(item["size"], bool) or item["size"] <= 0:
            raise UpdateTrustError(f"files.{kind}.size는 양의 정수여야 합니다.")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise UpdateTrustError(f"files.{kind}.sha256 형식이 64자리 16진수가 아닙니다.")
        if not isinstance(item["urls"], dict) or not item["urls"].get("gitlab") or not item["urls"].get("github"):
            raise UpdateTrustError(f"files.{kind}.urls에 gitlab과 github URL이 필요합니다.")

    return payload
