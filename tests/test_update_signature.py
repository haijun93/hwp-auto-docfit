import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from docfit_app.update_service import UpdateService
from docfit_core import update_signature as sig
from scripts import update_signing as tool
from tests.test_update_service import Network, manifest


def signed(private, data):
    data = dict(data)
    data['signature'] = base64.b64encode(private.sign(sig.canonical_bytes(data))).decode()
    return data


class SignatureTest(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.pub = tool.public_b64(self.key)

    def test_valid_passes(self):
        sig.verify_latest(signed(self.key, manifest()), self.pub)

    def test_tampered_rejected(self):
        data = signed(self.key, manifest())
        data['files']['setup']['sha256'] = 'a' * 64
        with self.assertRaises(sig.SignatureError):
            sig.verify_latest(data, self.pub)

    def test_other_key_rejected(self):
        with self.assertRaises(sig.SignatureError):
            sig.verify_latest(signed(Ed25519PrivateKey.generate(), manifest()), self.pub)

    def test_missing_or_bad_signature_rejected(self):
        for value in (None, '', '!!!', base64.b64encode(b'x').decode()):
            data = manifest()
            if value is not None:
                data['signature'] = value
            with self.assertRaises(sig.SignatureError):
                sig.verify_latest(data, self.pub)

    def test_no_public_key_rejected(self):
        with self.assertRaises(sig.SignatureError):
            sig.verify_latest(signed(self.key, manifest()), '')

    def test_flag_default_off(self):
        self.assertFalse(sig.enabled({}))
        self.assertTrue(sig.enabled({'DOCFIT_VERIFY_UPDATE_SIGNATURE': '1'}))
        self.assertFalse(sig.enabled({'DOCFIT_VERIFY_UPDATE_SIGNATURE': '0'}))


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def check(self, network, flag='1', pub=None):
        exe = Path(self.temp.name) / 'app' / 'HWP_AutoDocFit.exe'
        exe.parent.mkdir(exist_ok=True)
        service = UpdateService('1.80.5', folder=self.temp.name, executable=exe, frozen=True,
                                offline=lambda: False, http_get=network)
        env = {'DOCFIT_VERIFY_UPDATE_SIGNATURE': flag}
        with patch.dict(os.environ, env), patch.object(sig, 'UPDATE_PUBLIC_KEY_B64', pub or tool.public_b64(self.key)):
            service._refresh()
        return service.state()

    def net(self, data):
        n = Network()
        original = n.__call__
        import io
        def call(url, headers, timeout):
            if 'latest.json' in url:
                return io.BytesIO(json.dumps(data).encode())
            return original(url, headers, timeout)
        return call

    def test_signed_accepted(self):
        state = self.check(self.net(signed(self.key, manifest())))
        self.assertEqual(state['step'], 'available')

    def test_unsigned_rejected_without_fallback(self):
        state = self.check(self.net(manifest()))
        self.assertEqual(state['step'], 'failed')
        self.assertIn('서명', state['message'])

    def test_wrong_key_rejected_even_if_github_has_newer(self):
        n = Network(gitlab='1.80.6', github='1.80.9')
        import io
        inner = n.__call__
        data = signed(Ed25519PrivateKey.generate(), manifest())
        def call(url, headers, timeout):
            return io.BytesIO(json.dumps(data).encode()) if 'latest.json' in url else inner(url, headers, timeout)
        state = self.check(call)
        self.assertEqual(state['step'], 'failed')

    def test_flag_off_keeps_old_behavior(self):
        state = self.check(self.net(manifest()), flag='0')
        self.assertEqual(state['step'], 'available')


class ToolTest(unittest.TestCase):
    def test_keygen_sign_roundtrip_and_repo_path_refused(self):
        with tempfile.TemporaryDirectory() as d:
            keyfile = Path(d) / 'k' / 'update.key'
            pub = tool.keygen(keyfile)
            latest = Path(d) / 'latest.json'
            latest.write_text(json.dumps(manifest()), encoding='utf-8')
            self.assertEqual(tool.main(['sign', str(latest), '--key-file', str(keyfile)]), 0)
            sig.verify_latest(json.loads(latest.read_text(encoding='utf-8')), pub)
            with self.assertRaises(SystemExit):
                tool.keygen(keyfile)
        with self.assertRaises(SystemExit):
            tool.keygen(tool.ROOT / 'tmp_should_not_exist.key')
        with self.assertRaises(SystemExit):
            tool.load_private(None, {})

    def test_env_key(self):
        key = Ed25519PrivateKey.generate()
        env = {tool.ENV: base64.b64encode(tool.private_raw(key)).decode()}
        self.assertEqual(tool.public_b64(tool.load_private(None, env)), tool.public_b64(key))


if __name__ == '__main__':
    unittest.main()
