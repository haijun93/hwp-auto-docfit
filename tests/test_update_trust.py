"""Unit tests for Ed25519 signed update metadata verification (S1)."""
from __future__ import annotations

import base64
from datetime import datetime, timezone, timedelta
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from docfit_core.update_trust import (
    UpdateTrustError,
    UpdateTrustPolicy,
    verify_signed_manifest,
)


def _generate_key_pair():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, pub_bytes


def _make_signed_envelope(private_key, payload_dict, key_id="docfit-test-key"):
    payload_json = json.dumps(payload_dict, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")
    signed_data = b"HWP-AutoDocFit/update/v1\x00" + payload_bytes
    signature = private_key.sign(signed_data)
    envelope = {
        "schema": 1,
        "key_id": key_id,
        "payload": base64.b64encode(payload_bytes).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    return json.dumps(envelope).encode("utf-8")


class UpdateTrustTest(unittest.TestCase):
    def setUp(self):
        self.privkey, self.pubbytes = _generate_key_pair()
        self.policy = UpdateTrustPolicy(
            require_signed=True,
            public_keys={"docfit-test-key": self.pubbytes},
        )
        self.now = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
        self.valid_payload = {
            "product": "HWP_AutoDocFit",
            "version": "1.80.11",
            "issued_at": "2026-10-25T11:55:00Z",
            "expires_at": "2026-11-05T12:00:00Z",
            "files": {
                "portable": {
                    "name": "HWP_AutoDocFit_v1.80.11_Portable.exe",
                    "size": 50000000,
                    "sha256": "a" * 64,
                    "urls": {
                        "gitlab": "https://gitlab.aigov.go.kr/test/portable",
                        "github": "https://github.com/test/portable",
                    },
                },
                "setup": {
                    "name": "HWP_AutoDocFit_v1.80.11_Setup.exe",
                    "size": 60000000,
                    "sha256": "b" * 64,
                    "urls": {
                        "gitlab": "https://gitlab.aigov.go.kr/test/setup",
                        "github": "https://github.com/test/setup",
                    },
                },
            },
        }

    def test_valid_signature_success(self):
        env_bytes = _make_signed_envelope(self.privkey, self.valid_payload)
        manifest = verify_signed_manifest(env_bytes, policy=self.policy, now=self.now)
        self.assertEqual(manifest["version"], "1.80.11")
        self.assertEqual(manifest["product"], "HWP_AutoDocFit")
        self.assertIn("portable", manifest["files"])
        self.assertIn("setup", manifest["files"])

    def test_tampered_payload_rejected(self):
        env_bytes = _make_signed_envelope(self.privkey, self.valid_payload)
        env = json.loads(env_bytes.decode("utf-8"))
        # Tamper payload
        payload_data = json.loads(base64.b64decode(env["payload"]))
        payload_data["version"] = "9.99.99"
        tampered_bytes = json.dumps(payload_data).encode("utf-8")
        env["payload"] = base64.b64encode(tampered_bytes).decode("ascii")
        tampered_env_bytes = json.dumps(env).encode("utf-8")

        with self.assertRaises(UpdateTrustError):
            verify_signed_manifest(tampered_env_bytes, policy=self.policy, now=self.now)

    def test_expired_metadata_rejected(self):
        payload = dict(self.valid_payload)
        payload["issued_at"] = "2026-09-01T00:00:00Z"
        payload["expires_at"] = "2026-09-20T00:00:00Z"
        env_bytes = _make_signed_envelope(self.privkey, payload)

        with self.assertRaises(UpdateTrustError) as cm:
            verify_signed_manifest(env_bytes, policy=self.policy, now=self.now)
        self.assertIn("만료된", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
