import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from docfit_app.settings_service import SettingsService
from docfit_app.update_service import (
    UpdateService, RAW, GITHUB_API, DOWNLOAD_PAGE, extract_notes,
    parse_sha256sums, version_key, validate_url, setup_script, http_get, portable_target)


EXE = b'MZ' + b'x' * 140000
HASH = hashlib.sha256(EXE).hexdigest()


def manifest(version='1.80.6'):
    return {'version': version, 'files': {
        kind: {'name': f'HWP_AutoDocFit_v{version}_{suffix}.exe', 'size': len(EXE), 'sha256': HASH}
        for kind, suffix in [('portable', 'Portable'), ('setup', 'Setup')]}, 'notes': ['바뀐 점']}


class Network:
    def __init__(self, gitlab='1.80.6', github=None):
        self.gitlab, self.github, self.calls = gitlab, github, []
        self.data = EXE
        self.on_download = None

    def __call__(self, url, headers, timeout):
        self.calls.append((url, timeout))
        if 'latest.json' in url:
            if not self.gitlab:
                raise OSError('403')
            value = manifest(self.gitlab)
        elif url == GITHUB_API:
            if not self.github:
                raise OSError('차단')
            files = manifest(self.github)['files']
            value = {'tag_name': 'v' + self.github,
                     'assets': [{**f, 'browser_download_url': 'https://github.com/a/' + f['name']}
                                for f in files.values()] + [{'name': 'SHA256SUMS', 'browser_download_url': 'https://github.com/a/SHA256SUMS'}],
                     'body': '## 새로 된 점\n- **첫째**\n  - 하위\n- 둘째\n## 기타\n- 제외'}
        elif url.endswith('SHA256SUMS'):
            return io.BytesIO(('\n'.join(f'{HASH}  {f["name"]}' for f in manifest(self.github)['files'].values())).encode())
        else:
            if self.on_download:
                return self.on_download()
            return io.BytesIO(self.data)
        return io.BytesIO(json.dumps(value).encode())


class UpdateServiceTest(unittest.TestCase):
    def test_signed_sources_and_no_unsigned_downgrade(self):
        from datetime import datetime, timezone, timedelta
        from tests.test_update_trust import _generate_key_pair, _make_signed_envelope
        from docfit_core.update_trust import UpdateTrustPolicy
        private, public = _generate_key_pair()
        payload = manifest()
        now = datetime.now(timezone.utc)
        payload.update(product='HWP_AutoDocFit', issued_at=(now - timedelta(minutes=1)).isoformat(),
                       expires_at=(now + timedelta(days=1)).isoformat())
        for kind, item in payload['files'].items():
            item['urls'] = {'gitlab': RAW + 'signed-' + kind,
                            'github': 'https://github.com/a/signed-' + kind}
        envelope = _make_signed_envelope(private, payload)
        for required in (True, False):
            for source in ('gitlab', 'github'):
                for mode in ('valid', 'tampered', 'missing'):
                    with self.subTest(required=required, source=source, mode=mode):
                        calls = []
                        def network(url, headers, timeout):
                            calls.append(url)
                            if url == GITHUB_API:
                                return io.BytesIO(json.dumps({'assets': [] if mode == 'missing' else [
                                    {'name': 'latest.signed.json', 'browser_download_url':
                                     'https://github.com/a/latest.signed.json'}]}).encode())
                            if 'latest.signed.json' in url:
                                if mode == 'missing':
                                    raise OSError('404')
                                body = json.loads(envelope)
                                if mode == 'tampered':
                                    body['signature'] = 'A' * 88
                                return io.BytesIO(json.dumps(body).encode())
                            if source == 'github':
                                raise OSError('GitLab unavailable')
                            return Network()(url, headers, timeout)
                        service = self.service(network, trust_policy=UpdateTrustPolicy(
                            require_signed=required, public_keys={'docfit-test-key': public}))
                        if source == 'github':
                            service._gitlab = Mock(side_effect=OSError('unavailable'))
                        success = service.check()
                        expected = mode == 'valid' or (mode == 'missing' and not required and source == 'gitlab')
                        self.assertEqual(success, expected)
                        if mode == 'valid':
                            self.assertEqual(service._release['files']['portable']['url'],
                                             payload['files']['portable']['urls'][source])
                        if mode == 'tampered' or required:
                            self.assertFalse(any('latest.json?' in url or 'SHA256SUMS' in url for url in calls))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def service(self, network=None, installed=False, **kwargs):
        executable = self.folder / 'app' / 'HWP_AutoDocFit.exe'
        executable.parent.mkdir(exist_ok=True)
        if installed:
            (executable.parent / 'unins000.exe').touch()
        return UpdateService('1.80.5', folder=self.folder, executable=executable,
                             frozen=True, offline=lambda: False, http_get=network or Network(), **kwargs)

    def test_sources_choose_highest_and_gitlab_tie(self):
        for gl, gh, source, version in [('1.80.6', None, 'GitLab', '1.80.6'),
                (None, '1.80.6', 'GitHub', '1.80.6'), ('1.80.6', '1.80.6', 'GitLab', '1.80.6'),
                ('1.80.6', '1.81.0', 'GitHub', '1.81.0')]:
            with self.subTest(gl=gl, gh=gh):
                network = Network(gl, gh)
                service = self.service(network)
                self.assertTrue(service.check())
                self.assertEqual((source, version), (service.state()['source'], service.state()['latest']))
                self.assertTrue(all(0 < timeout <= 8 for _, timeout in network.calls))

    def test_failed_refresh_retains_previous_release_and_notes(self):
        network = Network()
        service = self.service(network)
        service.check()
        previous = service.state()
        network.gitlab = None
        self.assertFalse(service.check())
        state = service.state()
        self.assertEqual('failed', state['step'])
        for key in ('latest', 'notes', 'source'):
            self.assertEqual(previous[key], state[key])
        self.assertFalse(service.start_update())
        self.assertFalse(any(timeout == 30 for _, timeout in network.calls))

    def test_no_update_when_current_or_older(self):
        for v in ('1.80.5', '1.79.9'):
            service = self.service(Network(v))
            self.assertTrue(service.check())
            self.assertEqual('latest', service.state()['step'])

    def test_portable_refreshes_on_click_downloads_and_reuses(self):
        network, install = Network(), Mock()
        service = self.service(network, portable_install=install)
        service.check()
        network.gitlab = '1.80.7'
        self.assertTrue(service.start_update())
        path, digest = install.call_args.args
        self.assertEqual('HWP_AutoDocFit_v1.80.7_Portable.exe', path.name)
        self.assertEqual(HASH, digest)
        self.assertEqual(100, service.state()['percent'])
        self.assertEqual(EXE, path.read_bytes())
        self.assertFalse(list(path.parent.glob('*.part')))
        self.assertFalse(service.start_update())  # installer/replacement is already in progress
        service = self.service(network, portable_install=install)
        self.assertTrue(service.start_update())
        self.assertEqual(1, sum(timeout == 30 for _, timeout in network.calls))

    def test_installed_selects_setup_waits_and_exits(self):
        launch, exit_app = Mock(), Mock()
        service = self.service(installed=True, launch=launch, exit_app=exit_app)
        self.assertTrue(service.start_update())
        args = launch.call_args.args[0]
        self.assertIn("-EncodedCommand", args)
        self.assertNotIn("-File", args)
        if "-EncodedCommand" in args:
            import base64
            encoded = args[args.index("-EncodedCommand") + 1]
            decoded = base64.b64decode(encoded).decode("utf-16le")
            self.assertIn("_Setup.exe", decoded)
            self.assertIn(f"'WaitPidList' = '{os.getpid()} {os.getppid()}'", decoded)
            self.assertIn(f"'Sha256' = '{HASH}'", decoded)
            self.assertIn("Installer", decoded)
            self.assertFalse(list(self.folder.rglob('*.ps1')))
        exit_app.assert_called_once()
        script = setup_script()
        self.assertLess(script.index('Wait-Process'), script.index('Start-Process'))
        self.assertIn('/SILENT /NORESTART /SUPPRESSMSGBOXES /SP-', script)
        self.assertIn('(Get-Sha256Hex $Installer)', script)   # Get-FileHash 없는 PowerShell에서도 검증(2026-10-23 CI)
        self.assertNotIn('Get-FileHash -LiteralPath', script)

    def test_corrupt_hash_size_mz_rejected_and_invalid_cache_redownloaded(self):
        for data in (b'MZ' + b'y' * 140000, b'ZZ' + EXE[2:], EXE[:-1], EXE + b'x'):
            with self.subTest(data=data[:3], length=len(data)):
                network, install = Network(), Mock()
                network.data = data
                service = self.service(network, portable_install=install)
                self.assertFalse(service.start_update())
                self.assertEqual('failed', service.state()['step'])
                install.assert_not_called()
                self.assertFalse(list((self.folder / 'updates').glob('*.part')))
        path = self.folder / 'updates' / manifest()['files']['portable']['name']
        path.write_bytes(b'bad cache')
        service = self.service(portable_install=Mock())
        self.assertTrue(service.start_update())
        self.assertEqual(EXE, path.read_bytes())

    def test_progress_updates_during_reads(self):
        network, values = Network(), []
        service = self.service(network, portable_install=Mock())
        class Response(io.BytesIO):
            def read(self, n=-1):
                values.append(service.state()['percent'])
                return super().read(n)
            read1 = read
        network.on_download = lambda: Response(EXE)
        self.assertTrue(service.start_update())
        self.assertTrue(any(0 < p < 100 for p in values))
        self.assertEqual(100, values[-1])

    def test_stall_and_socket_timeout_fail_cleanup(self):
        network = Network()
        now = [0]
        service = self.service(network, portable_install=Mock(), clock=lambda: now[0])
        class Stalled(io.BytesIO):
            def read(self, n=-1):
                now[0] += 31
                return super().read(n)
            read1 = read
        network.on_download = lambda: Stalled(EXE)
        self.assertFalse(service.start_update())
        self.assertIn('30초', service.state()['message'])
        self.assertIn(30, [timeout for _, timeout in network.calls])
        def timeout():
            raise TimeoutError('응답 시간 초과')
        network.on_download = timeout
        self.assertFalse(service.start_update())
        self.assertFalse(list((self.folder / 'updates').glob('*.part')))

    def test_active_download_can_last_over_30_seconds(self):
        network, now = Network(), [0]
        service = self.service(network, portable_install=Mock(), clock=lambda: now[0])
        class Active(io.BytesIO):
            def read(self, n=-1):
                now[0] += 20
                return super().read(n)
            read1 = read
        network.on_download = lambda: Active(EXE)
        self.assertTrue(service.start_update())
        self.assertGreater(now[0], 30)

    def test_offline_zero_calls_all_entries_and_order(self):
        for installed in (False, True):
            network, page = Network(), Mock()
            service = self.service(network, installed=installed, open_page=page)
            service.offline = lambda: True
            self.assertFalse(service.check())
            self.assertFalse(service.start_update())
            self.assertFalse(service.open_download_page())
            self.assertEqual([], network.calls)
            page.assert_not_called()
            state = service.state()
            self.assertEqual('offline', state['step'])
            self.assertIn('Setup.exe', state['message'])
            self.assertIn('포터블', state['message'])
            self.assertEqual(installed, state['message'].index('Setup.exe') < state['message'].index('포터블'))

    def test_switch_offline_during_download_cleans_part(self):
        network = Network()
        service = self.service(network, portable_install=Mock())
        class Switch(io.BytesIO):
            def read(self, n=-1):
                service.offline = lambda: True
                return super().read(n)
            read1 = read
        network.on_download = lambda: Switch(EXE)
        self.assertFalse(service.start_update())
        self.assertEqual('offline', service.state()['step'])
        self.assertFalse(list((self.folder / 'updates').glob('*.part')))

    def test_version_notice_once_and_settings_kept(self):
        store = SettingsService(self.folder / 'settings.json')
        store.update(lambda s: s.update(last_run_version='1.80.4', my_setting='keep'))
        service = self.service()
        self.assertEqual('v1.80.4 → v1.80.5으로 바뀌었어요', service.version_notice(store))
        self.assertIsNone(service.version_notice(store))
        self.assertIsNone(self.service().version_notice(store))
        self.assertEqual('keep', store.read()['my_setting'])

    def test_first_run_records_version_without_notice(self):
        store = SettingsService(self.folder / 'settings.json')
        self.assertIsNone(self.service().version_notice(store))
        self.assertEqual('1.80.5', store.read()['last_run_version'])

    def test_portable_replaces_outer_launcher_and_keeps_appdata_settings(self):
        launcher = self.folder / 'Portable.exe'
        launcher.write_bytes(b'old launcher')
        cached = self.folder / 'cache' / 'HWP_AutoDocFit.exe'
        cached.parent.mkdir()
        cached.write_bytes(b'cached app')
        with patch.dict(os.environ, {'APPDATA': str(self.folder / 'roaming')}):
            old = UpdateService('1.80.5', executable=cached, frozen=True, offline=lambda: True)
            store = SettingsService(old.folder / 'settings.json')
            store.update(lambda s: s.update(last_run_version='1.80.5', user_setting='keep'))
            settings_before = (old.folder / 'settings.json').read_bytes()
            target = portable_target(cached, {'DOCFIT_LAUNCHER_PATH': str(launcher)})
            self.assertEqual(launcher.resolve(), target)
            target.write_bytes(EXE)
            new = UpdateService('1.80.6', executable=cached, frozen=True, offline=lambda: True)
            self.assertEqual(old.folder, new.folder)
            self.assertEqual(settings_before, (new.folder / 'settings.json').read_bytes())
            self.assertIn('1.80.5 → v1.80.6', new.version_notice(store))
            self.assertEqual('keep', store.read()['user_setting'])
        self.assertEqual(cached.resolve(), portable_target(cached, {}))
        self.assertEqual(b'cached app', cached.read_bytes())

    def test_busy_and_document_job_refuse_start(self):
        network = Network()
        service = self.service(network, running=lambda: True)
        self.assertFalse(service.start_update())
        self.assertFalse(network.calls)
        service.running = lambda: False
        service._operation.acquire()
        self.addCleanup(service._operation.release)
        self.assertFalse(service.start_update())
        self.assertFalse(service.check())
        self.assertFalse(network.calls)

    def test_installer_in_progress_refuses_check_and_second_start(self):
        network, launch = Network(), Mock()
        service = self.service(network, installed=True, launch=launch)
        self.assertTrue(service.start_update())
        previous_calls = len(network.calls)
        self.assertFalse(service.start_update())
        self.assertFalse(service.check())
        launch.assert_called_once()
        self.assertEqual(previous_calls, len(network.calls))

    def test_metadata_deadline_moves_to_other_source(self):
        network, now = Network('1.80.7', '1.80.6'), [0]
        service = self.service(network, clock=lambda: now[0])
        original = service.http_get
        class Slow(io.BytesIO):
            def read1(self, n=-1):
                now[0] += 9
                return super().read(n)
        def get(url, headers, timeout):
            response = original(url, headers, timeout)
            if 'latest.json' in url:
                return Slow(response.getvalue())
            return response
        service.http_get = get
        self.assertTrue(service.check())
        self.assertEqual('GitHub', service.state()['source'])

    def test_state_is_a_copy(self):
        service = self.service()
        service.check()
        state = service.state()
        state['notes'].clear()
        self.assertEqual(['바뀐 점'], service.state()['notes'])

    def test_setup_script_skips_unrelated_parent_without_executing_installer(self):
        installer = self.folder / 'Setup.exe'
        installer.write_bytes(EXE)
        # Override only process launch; real PowerShell parses parameters and verifies the hash.
        script = self.folder / 'wait-test.ps1'
        body = setup_script()
        insert = body.index("$ErrorActionPreference")
        body = body[:insert] + "function Start-Process { param($FilePath, $ArgumentList, [switch]$Wait) Write-Output $ArgumentList }\n" + body[insert:]
        script.write_text(body, encoding='utf-8-sig')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script),
                                 '-Installer', str(installer), '-Sha256', HASH,
                                 '-WaitPidList', str(os.getpid()), '-AppPid', '2147483646',
                                 '-AppExecutable', str(self.folder / 'HWP_AutoDocFit.exe')],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(b'/SILENT /NORESTART /SUPPRESSMSGBOXES /SP-', result.stdout)

    def test_source_opens_download_page_without_download(self):
        network, page = Network(), Mock()
        service = self.service(network, open_page=page)
        service.frozen = False
        self.assertTrue(service.start_update())
        page.assert_called_once_with(DOWNLOAD_PAGE)
        self.assertFalse(network.calls)

    def test_cancelled_launch_and_failed_portable_callback(self):
        error = OSError('cancel')
        error.winerror = 1223
        service = self.service(installed=True, launch=Mock(side_effect=error))
        self.assertFalse(service.start_update())
        self.assertEqual('cancelled', service.state()['step'])
        service = self.service(installed=True, launch=Mock(side_effect=OSError()))
        self.assertFalse(service.start_update())
        self.assertEqual('failed', service.state()['step'])
        (self.folder / 'app' / 'unins000.exe').unlink()
        service = self.service(portable_install=lambda *a: False)
        self.assertFalse(service.start_update())
        self.assertEqual('failed', service.state()['step'])

    def test_periodic_offline_and_disabled_schedule_without_http(self):
        network, calls = Network(), []
        service = self.service(network)
        service.offline = lambda: True
        schedule = lambda delay, callback: calls.append((delay, callback))
        service.start_periodic_checks(schedule, lambda: True, Mock())
        self.assertEqual(20000, calls[0][0])
        calls[0][1]()
        self.assertEqual(21600000, calls[-1][0])
        self.assertFalse(network.calls)

    def test_periodic_announces_each_version_once(self):
        network, scheduled, announce = Network(), [], Mock()
        service = self.service(network)
        service.start_periodic_checks(lambda d, cb: scheduled.append((d, cb)), lambda: True, announce)
        # Run worker synchronously; HTTP remains fake.
        class Worker:
            def __init__(self, target, **kwargs): self.target = target
            def start(self): self.target()
        with patch('docfit_app.update_service.threading.Thread', Worker):
            scheduled[0][1]()
            next(cb for delay, cb in scheduled if delay == 0)()
            self.assertEqual(1, announce.call_count)
            scheduled[-1][1]()
            self.assertEqual(1, sum(delay == 0 for delay, _ in scheduled))


class ParsingTest(unittest.TestCase):
    def test_versions(self):
        self.assertGreater(version_key('1.80.10'), version_key('v1.80.9'))
        self.assertGreater(version_key('1.81.0'), version_key('1.81.0-beta.2'))
        self.assertGreater(version_key('1.81.0-beta.10'), version_key('1.81 Alpha 2'))
        with self.assertRaises(ValueError): version_key('nightly')

    def test_notes(self):
        body = '# 발행\n- 제외\n## 새로 된 점\n' + '\n'.join(f'- **항목{i}**\n  - 하위' for i in range(8)) + '\n## 기타\n- 제외'
        self.assertEqual([f'항목{i}' for i in range(6)], extract_notes(body))

    def test_sums(self):
        self.assertEqual({'a.exe': HASH, 'b.exe': HASH}, parse_sha256sums(f'{HASH.upper()}  a.exe\n{HASH} *b.exe\n잘못된 줄'))
        # 실제 릴리스의 SHA256SUMS는 빌드 폴더 경로가 붙어 있다(2026-10-23 실측: 경로 때문에 GitHub 조회가 실패).
        self.assertEqual({'HWP_AutoDocFit_v1.80.4_Portable.exe': HASH},
                         parse_sha256sums(f'{HASH} *release-assets/HWP_AutoDocFit_v1.80.4_Portable.exe'))

    def test_url_restrictions(self):
        for url in ('http://github.com/a', 'https://github.com.evil.org/a', 'https://evil.org/a', 'https://github.com:999/a', 'https://user:pass@github.com/a'):
            with self.assertRaises(ValueError): validate_url(url)

    def test_redirect_revalidated_without_connecting_outside(self):
        response = Mock(status=302)
        response.getheader.return_value = 'https://evil.org/payload'
        connection = Mock()
        connection.getresponse.return_value = response
        with patch('docfit_app.update_service.http.client.HTTPSConnection', return_value=connection) as constructor:
            with self.assertRaises(ValueError): http_get(GITHUB_API, {}, 8)
            self.assertEqual(1, constructor.call_count)
        connection.close.assert_called()


class IntegrationTest(unittest.TestCase):
    def test_bridge_update_contract_and_document_job_guard(self):
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        from types import SimpleNamespace
        service = Mock()
        service.state.return_value = {'step': 'available'}
        gui = SimpleNamespace(running=True, _업데이트_서비스=lambda: service)
        bridge = DesktopWebBridge(gui)
        bridge._tk = lambda callback: callback()
        api = _BrowserApi(bridge)
        self.assertEqual('JOB_RUNNING', api.start_update()['error']['code'])
        service.start_update.assert_not_called()
        gui.running = False
        service.state.return_value = {'step': 'installing'}
        self.assertEqual('BUSY', api.start_update()['error']['code'])
        with patch('desktop_web_ui.threading.Thread') as worker:
            api.check_update()
            self.assertEqual(service.check, worker.call_args.kwargs['target'])
            service.state.return_value = {'step': 'available'}
            api.start_update()
            self.assertEqual(service.start_update, worker.call_args.kwargs['target'])
        api.open_update_page()
        service.open_download_page.assert_called_once()

    def test_publish_writes_manifest_without_network_or_git_mutations(self):
        from scripts import publish_gitlab_downloads as publish
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            work = root / 'downloads'
            work.mkdir()
            (root / 'releases').mkdir()
            (root / 'releases' / 'v1.80.6.md').write_text('## 새로 된 점\n- **공통 안내**\n  - 제외\n', encoding='utf-8')
            example = root / 'example.txt'
            example.write_text('example', encoding='utf-8')
            captured = []
            def curl(args, **kwargs):
                path = Path(args[args.index('--output') + 1])
                if path.name == 'SHA256SUMS':
                    path.write_text('\n'.join(f'{HASH}  {item["name"]}' for item in manifest()['files'].values()), encoding='utf-8')
                else:
                    path.write_bytes(EXE)
            def git(path, *args):
                if args == ('add', '-A'):
                    captured.append(json.loads((path / 'latest.json').read_text(encoding='utf-8')))
            with patch.object(publish, 'ROOT', root), patch.object(publish, 'EXAMPLE', example), \
                    patch.object(publish.tempfile, 'mkdtemp', return_value=str(work)), \
                    patch.object(publish.subprocess, 'run', side_effect=curl), patch.object(publish, '_git', side_effect=git):
                self.assertEqual(0, publish.main('1.80.6'))
            self.assertEqual(manifest()['files'], captured[0]['files'])
            self.assertEqual(['공통 안내'], captured[0]['notes'])


if __name__ == '__main__':
    unittest.main()
