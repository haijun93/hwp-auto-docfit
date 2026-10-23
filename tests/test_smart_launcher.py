import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid
import unittest
import zipfile
from unittest.mock import patch

from scripts.build_smart_launcher import build, find_csc, make_payload


ROOT = Path(__file__).resolve().parents[1]


class SmartLauncherBuildTest(unittest.TestCase):
    def test_payload_is_manifested_and_app_exe_is_renamed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "HWP_AutoDocFit.exe").write_bytes(b"app executable")
            (bundle / "nested").mkdir()
            (bundle / "nested" / "library.dll").write_bytes(b"library")
            archive = root / "payload.zip"

            payload_hash, manifest = make_payload(bundle, archive, "9.99.99-test")

            self.assertEqual(len(payload_hash), 64)
            self.assertEqual(payload_hash, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertTrue(zipfile.is_zipfile(archive))
            with zipfile.ZipFile(archive) as zipped:
                self.assertEqual(set(zipped.namelist()), {"app_main.exe", "nested/library.dll"})
                self.assertEqual(zipped.read("app_main.exe"), b"app executable")
                self.assertIsNone(zipped.testzip())
            manifest_text = manifest.read_text(encoding="utf-8")
            self.assertIn(f"P\t{payload_hash}\n", manifest_text)
            self.assertIn("F\t", manifest_text)
            self.assertIn("\tapp_main.exe\n", manifest_text)

    def test_launcher_implements_safe_extract_cache_and_mutex_handoff(self):
        source = (ROOT / "launcher" / "smart_launcher.cs").read_text(encoding="utf-8")
        app_source = (ROOT / "hwp-auto-docfit.py").read_text(encoding="utf-8")
        build_source = (ROOT / "build_dist.bat").read_text(encoding="utf-8")

        for token in (
            "CacheIsValid", "ExtractPayload", "SafeCombine", "SHA256.Create()",
            "Directory.Move(staging, finalPath)", "CleanupOldCaches", "ProcessStartInfo",
            "SetForegroundWindow", r'mutexName = "Global\\" + MutexSuffix',
            'GetManifestResourceStream("DocFitSplash")', "new SplashForm(manifest.Version)",
        ):
            self.assertIn(token, source)
        self.assertIn("DOCFIT_LAUNCHER_HANDOFF_EVENT", app_source)
        self.assertIn("WaitForSingleObject(handle, 45000)", app_source)
        self.assertIn("CreateMutexW(None, True, mutex_name)", app_source)
        self.assertIn("scripts\\build_smart_launcher.py", build_source)

    def test_cli_routing_and_relative_gui_arguments(self):
        source = (ROOT / 'launcher' / 'smart_launcher.cs').read_text(encoding='utf-8')
        self.assertIn('bool cliCommand = IsCliCommand(args);', source)
        self.assertIn('!File.Exists(args[0]) && !Directory.Exists(args[0])', source)
        for alias in ('--help', '-h', '/?', '--version'):
            self.assertIn('"' + alias + '"', source)
        self.assertIn('File.Exists(a) || Directory.Exists(a) ? Path.GetFullPath(a) : a', source)
        self.assertIn('WorkingDirectory = IsCliCommand(args) ? Environment.CurrentDirectory : cachePath', source)

    def test_cleanup_protects_running_newer_and_unmovable_caches(self):
        source = (ROOT / 'launcher' / 'smart_launcher.cs').read_text(encoding='utf-8')
        cleanup = source.split('private static void CleanupOldCaches(', 1)[1].split(
            'private static Version CacheVersion(', 1)[0]
        self.assertIn('candidateVersion == null || candidateVersion > currentVersion', cleanup)
        self.assertIn('if (CacheIsInUse(path)) continue;', cleanup)
        self.assertIn('try { Directory.Move(path, trash); }\n            catch { continue; }', cleanup)
        self.assertLess(cleanup.index('Directory.Move(path, trash)'), cleanup.index('Directory.Delete(trash, true)'))
        self.assertNotIn('Directory.Delete(path, true)', cleanup)
        self.assertIn('Process.GetProcessesByName("app_main")', source)
        self.assertIn('process.MainModule.FileName', source)
        self.assertIn('catch { inUse = true; }', source)
        self.assertIn('FileMode.Open, FileAccess.Write, FileShare.None', source)
        self.assertIn('"python312.dll"', source)
        self.assertIn('"*.pyd", SearchOption.AllDirectories', source)
        validity = source.split('private static bool CacheIsValid(', 1)[1].split(
            'private static void ExtractPayload(', 1)[0]
        self.assertIn('foreach (ManifestItem item in manifest.Items)', validity)
        self.assertIn('!info.Exists || info.Length != item.Length', validity)

    @unittest.skipUnless(os.name == 'nt', 'Windows cache cleanup integration test')
    def test_compiled_cleanup_preserves_locked_running_and_newer_caches(self):
        # Compile the real launcher with a test-only entry point; never use the user's cache.
        with tempfile.TemporaryDirectory(prefix='docfit-cache-cleanup-') as temporary:
            root = Path(temporary)
            harness = root / 'CleanupProbe.cs'
            harness.write_text('''
using System;
using System.Reflection;
using System.Threading;
internal static class CleanupProbe {
    public static void Main(string[] args) {
        if (args[0] == "hold") {
            Console.WriteLine("ready");
            Thread.Sleep(60000);
            return;
        }
        typeof(SmartLauncher).GetMethod("CleanupOldCaches",
            BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { args[0], args[1] });
    }
}
''', encoding='utf-8')
            probe = root / 'probe.exe'
            subprocess.run([
                str(find_csc()), '/nologo', '/codepage:65001', '/target:exe', '/main:CleanupProbe',
                f'/out:{probe}', '/reference:System.Windows.Forms.dll',
                '/reference:System.IO.Compression.dll', '/reference:System.Core.dll',
                str(ROOT / 'launcher' / 'smart_launcher.cs'), str(harness),
            ], check=True, timeout=30)
            cache = root / 'cache'
            cache.mkdir()
            keep = 'app_v1.80.9_current'

            def make_cache(name):
                path = cache / name
                (path / '_internal').mkdir(parents=True)
                (path / 'asset.txt').write_bytes(b'keep all assets')
                return path

            def snapshot(path):
                return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}

            def cleanup():
                subprocess.run([str(probe), str(cache), keep], check=True, timeout=30)

            current = make_cache(keep)
            newer = make_cache('app_v1.80.10_newer')
            unknown = make_cache('app_vunknown_hash')
            staging = make_cache('.staging-active')
            protected = [current, newer, unknown, staging]
            for filename in ('_internal/python312.dll', '_internal/extension.pyd', 'asset.txt'):
                with self.subTest(locked_file=filename):
                    locked = make_cache('app_v1.80.8_locked')
                    free = make_cache('app_v1.79.0_unused')
                    target = locked / filename
                    target.write_bytes(b'locked payload')
                    before = snapshot(locked)
                    # Windows open() denies delete sharing. asset.txt reaches the failed Move branch.
                    with target.open('rb'):
                        cleanup()
                        self.assertEqual(snapshot(locked), before)
                        self.assertFalse(free.exists())
                        self.assertTrue(all(p.exists() for p in protected))
                        self.assertFalse(list(cache.glob('.trash-*')))
                    cleanup()
                    self.assertFalse(locked.exists())

            running = make_cache('app_v1.80.8_running')
            shutil.copy2(probe, running / 'app_main.exe')
            before = snapshot(running)
            child = subprocess.Popen([str(running / 'app_main.exe'), 'hold'], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'ready')
                cleanup()
                self.assertEqual(snapshot(running), before)
            finally:
                child.terminate()
                child.wait(timeout=10)
                child.stdout.close()
            cleanup()
            self.assertFalse(running.exists())

    def test_splash_image_has_no_baked_status_text(self):
        """그림 속 옛 버전·진행 막대·상태 문구가 런처 글과 겹치지 않게(1.80.3 사용자 보고)."""
        from PIL import Image

        image = Image.open(ROOT / "resources" / "splash.png").convert("RGB")
        # 버전 줄은 왼쪽 고양이 그림(x<119)을 빼고, 진행 막대·상태 줄은 좌우 테두리만 빼고 비어 있어야 한다.
        for left, top, bottom in ((119, 82, 99), (4, 166, 181), (4, 194, 215)):
            for y in range(top, bottom + 1):
                for x in range(left, image.width - 4):
                    self.assertEqual(image.getpixel((x, y)), (255, 255, 255), (x, y))
        source = (ROOT / "launcher" / "smart_launcher.cs").read_text(encoding="utf-8")
        self.assertNotIn("Color.Transparent", source)
        self.assertIn("Left = 119, Top = 82", source)
        self.assertIn("Left = 34, Top = 194", source)

    def test_ci_enforces_warm_ui_startup_target(self):
        workflow = (ROOT / ".github" / "workflows" / "build-windows-exe.yml").read_text(encoding="utf-8")
        smoke = (ROOT / "scripts" / "smoke_smart_launcher.py").read_text(encoding="utf-8")
        self.assertIn("--target-cache-ms 1500 --target-splash-ms 100 @targetGate", workflow)
        self.assertIn("refs/heads/release/*", workflow)
        self.assertIn("@('--require-target')", workflow)
        self.assertIn('"warm_ui_first_within_target"', smoke)
        self.assertIn('"warm_ui_second_within_target"', smoke)
        self.assertIn('"cold_ui_splash_within_target"', smoke)

    @unittest.skipUnless(os.name == "nt", "Windows launcher integration test")
    def test_compiled_launcher_forwards_arguments_and_hands_off_mutex(self):
        csc = find_csc()
        fixture = ROOT / "tests" / "fixtures" / "smart_launcher_child.cs"
        version = "9.98.0-test" + uuid.uuid4().hex[:8]
        cache_path = None
        with tempfile.TemporaryDirectory(prefix="docfit-launcher-integration-") as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            bundle.mkdir()
            child = bundle / "HWP_AutoDocFit.exe"
            (bundle / 'asset.txt').write_bytes(b'complete asset')
            subprocess.run([str(csc), "/nologo", "/target:exe", f"/out:{child}", str(fixture)], check=True)
            launcher = root / "HWP_AutoDocFit.exe"
            # 사용 중인 앱과 충돌하지 않도록 시험용 런처 소스의 뮤텍스 이름만 격리한다.
            test_mutex = 'HWP_AutoDocFit_Test_' + uuid.uuid4().hex
            isolated = root / 'compiler-root'
            (isolated / 'launcher').mkdir(parents=True)
            (isolated / 'resources').mkdir()
            launcher_source = (ROOT / 'launcher' / 'smart_launcher.cs').read_text(encoding='utf-8')
            cache_parent = root / 'test-cache'
            launcher_source = launcher_source.replace('HWP_AutoDocFit_SingleInstance_Mutex', test_mutex)
            launcher_source = launcher_source.replace(
                'Path.Combine(localAppData, "HWP_AutoDocFit")',
                '@"' + str(cache_parent).replace('"', '""') + '"')
            (isolated / 'launcher' / 'smart_launcher.cs').write_text(launcher_source, encoding='utf-8')
            for name in ('app_icon.ico', 'splash.png'):
                shutil.copy2(ROOT / 'resources' / name, isolated / 'resources' / name)
            with patch('scripts.build_smart_launcher.ROOT', isolated):
                payload_hash, _ = build(bundle, launcher, version)
            cache_name = "app_v" + version.replace(" ", "_") + "_" + payload_hash[:12]
            cache_path = cache_parent / cache_name

            # First non-self-test launch exercises the embedded native splash
            # resource and cold extraction, then transfers the mutex to the child.
            handoff_report = root / "mutex handoff.json"
            handoff_report.write_text('', encoding='utf-8')
            subprocess.run([str(launcher), "--handoff-report", handoff_report.name], cwd=root, check=True, timeout=30)
            deadline = time.monotonic() + 5
            while handoff_report.read_text(encoding="utf-8") != '{"handoff":true}' and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(handoff_report.read_text(encoding="utf-8"), '{"handoff":true}')
            self.assertTrue((cache_path / ".docfit-complete").is_file())

            report = root / "report path with spaces.json"
            subprocess.run(
                [str(launcher), "--self-test", "--self-test-report", str(report), "argument with spaces"],
                check=True, timeout=30,
            )
            self.assertEqual(report.read_text(encoding="utf-8"), '{"ok":true}')
            marker_time = (cache_path / ".docfit-complete").stat().st_mtime_ns
            warm_start = time.perf_counter()
            subprocess.run(
                [str(launcher), "--self-test", "--self-test-report", str(report), "argument with spaces"],
                check=True, timeout=30,
            )
            cached_ms = (time.perf_counter() - warm_start) * 1000
            self.assertEqual((cache_path / ".docfit-complete").stat().st_mtime_ns, marker_time)

            # A completion marker alone must not accept a partially deleted cache.
            asset = cache_path / 'asset.txt'
            for damage in ('missing', 'truncated'):
                with self.subTest(cache_damage=damage):
                    if damage == 'missing':
                        asset.unlink()
                    else:
                        asset.write_bytes(b'x')
                    subprocess.run(
                        [str(launcher), '--self-test', '--self-test-report', str(report), 'argument with spaces'],
                        check=True, timeout=30,
                    )
                    self.assertEqual(asset.read_bytes(), b'complete asset')

            # CLI는 앱 뮤텍스가 잡힌 상태에서도 실행되고 자식 종료 코드·런처 경로를 보존한다.
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.windll.kernel32
            kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
            kernel.CreateMutexW.restype = wintypes.HANDLE
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
            handle = kernel.CreateMutexW(None, True, 'Global\\' + test_mutex)
            self.assertTrue(handle)
            try:
                cli_report = root / 'CLI 경로 report.txt'
                completed = subprocess.run([str(launcher), 'convert', cli_report.name], cwd=root, timeout=30)
                self.assertEqual(completed.returncode, 7)
                self.assertEqual(cli_report.read_text(encoding='utf-8'), str(launcher))
            finally:
                kernel.ReleaseMutex(handle)
                kernel.CloseHandle(handle)
            self.assertGreater(cached_ms, 0)
            time.sleep(1.1)  # let the fixture release its mutex and executable image handle



if __name__ == "__main__":
    unittest.main()
