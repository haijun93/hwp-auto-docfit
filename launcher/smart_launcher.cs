using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

internal static class SmartLauncher
{
    private const string AppTitle = "한글편집 후처리 (HWP_AutoDocFit)";
    private const string PayloadResource = "DocFitPayload";
    private const string ManifestResource = "DocFitManifest";
    private const string MutexSuffix = "HWP_AutoDocFit_SingleInstance_Mutex";
    private const int SwRestore = 9;
    private static NativeSplash splash;
    // 시험 전용: 시작 단계 시각 기록(ms, 프로세스 시작 기준)과 사용자 캐시·뮤텍스와 겹치지 않는 시험 폴더.
    private static readonly string TracePath = Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_TRACE");
    private static readonly string TestRoot = Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_TEST_ROOT");

    private static void Trace(string stage)
    {
        if (string.IsNullOrEmpty(TracePath)) return;
        try
        {
            double ms = (DateTime.Now - Process.GetCurrentProcess().StartTime).TotalMilliseconds;
            File.AppendAllText(TracePath, stage + "\t" + ms.ToString("0.0", CultureInfo.InvariantCulture) + "\n");
        }
        catch { }
    }

    private static bool IsCliCommand(string[] args)
    {
        return args.Length > 0 &&
            Array.IndexOf(new[] { "convert", "help", "version", "formats", "--help", "-h", "/?", "--version" }, args[0]) >= 0 &&
            !File.Exists(args[0]) && !Directory.Exists(args[0]);
    }

    [STAThread]
    private static int Main(string[] args)
    {
        Trace("main");
        bool cliCommand = IsCliCommand(args);
        // GUI 파일 인자는 호출 폴더 기준이다. 리소스용 cachePath 작업 폴더는 유지한다.
        // 스플래시 전에는 LINQ(System.Core)를 쓰지 않는다: 어셈블리를 더 불러오면 첫 화면이 늦어진다.
        bool selfTest = false;
        for (int i = 0; i < args.Length; i++)
        {
            if (!cliCommand && (File.Exists(args[i]) || Directory.Exists(args[i]))) args[i] = Path.GetFullPath(args[i]);
            if (string.Equals(args[i], "--self-test", StringComparison.OrdinalIgnoreCase)) selfTest = true;
        }
        if (cliCommand) AttachConsole(unchecked((uint)-1));
        string mutexName = null;
        Mutex mutex = null;
        bool ownsMutex = false;
        string cachePath = null;

        try
        {
            // 버전·해시 머리 두 줄만 먼저 읽어 캐시 폴더를 정한다. 첫 실행이면 전체 매니페스트를
            // 읽기 전에 스플래시부터 띄운다.
            string version, payloadHash;
            ReadManifestHeader(out version, out payloadHash);
            PayloadManifest manifest = null;
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string cacheRoot = string.IsNullOrEmpty(TestRoot) ? Path.Combine(localAppData, "HWP_AutoDocFit") : TestRoot;
            Directory.CreateDirectory(cacheRoot);
            cachePath = Path.Combine(cacheRoot, "app_v" + SafeVersion(version) + "_" + payloadHash.Substring(0, 12));

            if (!selfTest && !cliCommand)
            {
                mutexName = "Global\\" + MutexSuffix + (string.IsNullOrEmpty(TestRoot) ? "" : "_Test");
                try
                {
                    mutex = new Mutex(true, mutexName, out ownsMutex);
                }
                catch
                {
                    mutexName = "Local\\" + MutexSuffix + (string.IsNullOrEmpty(TestRoot) ? "" : "_Test");
                    mutex = new Mutex(true, mutexName, out ownsMutex);
                }
                if (!ownsMutex)
                {
                    mutex.Dispose();
                    ActivateExistingWindow();
                    if (args.Length > 0)
                    {
                        manifest = LoadManifest(version, payloadHash);
                        if (!CacheIsValid(cachePath, manifest)) ExtractPayload(cachePath, manifest, true);
                        bool ignored = false;
                        return StartApplication(Path.Combine(cachePath, "app_main.exe"), cachePath,
                            args, true, null, null, ref ignored);
                    }
                    return 0;
                }
            }

            bool interactive = !selfTest && !cliCommand;
            Trace("header");
            if (interactive && !File.Exists(Path.Combine(cachePath, ".docfit-complete"))) ShowSplash(version);
            manifest = LoadManifest(version, payloadHash);
            Trace("manifest");
            if (!CacheIsValid(cachePath, manifest))
            {
                if (interactive && splash == null) ShowSplash(version);
                ExtractPayload(cachePath, manifest, selfTest || cliCommand);
            }

            string appPath = Path.Combine(cachePath, "app_main.exe");
            int exitCode = StartApplication(appPath, cachePath, args, selfTest || cliCommand, mutex, mutexName, ref ownsMutex);
            mutex = null;
            if (!selfTest && !cliCommand) CleanupOldCaches(cacheRoot, Path.GetFileName(cachePath));
            return exitCode;
        }
        catch (Exception ex)
        {
            CloseSplash();
            if (!cliCommand && !args.Any(a => string.Equals(a, "--self-test", StringComparison.OrdinalIgnoreCase)))
            {
                MessageBoxW(IntPtr.Zero, "앱 실행 준비 중 오류가 발생했습니다.\r\n\r\n" + ex.Message, AppTitle, 0x10);
            }
            return 1;
        }
        finally
        {
            CloseSplash();
            if (ownsMutex && mutex != null)
            {
                try { mutex.ReleaseMutex(); } catch { }
            }
            if (mutex != null) mutex.Dispose();
        }
    }

    private static int StartApplication(string appPath, string cachePath, string[] args,
        bool selfTest, Mutex mutex, string mutexName, ref bool ownsMutex)
    {
        string eventName = null;
        EventWaitHandle handoff = null;
        Process process = null;
        try
        {
            var start = new ProcessStartInfo
            {
                FileName = appPath,
                WorkingDirectory = IsCliCommand(args) ? Environment.CurrentDirectory : cachePath,
                UseShellExecute = false,
                Arguments = string.Join(" ", args.Select(QuoteArgument).ToArray())
            };
            start.EnvironmentVariables["DOCFIT_LAUNCHER_PATH"] = Assembly.GetExecutingAssembly().Location;
            if (selfTest)
            {
                start.EnvironmentVariables.Remove("DOCFIT_LAUNCHER_HANDOFF_EVENT");
                start.EnvironmentVariables.Remove("DOCFIT_LAUNCHER_MUTEX_NAME");
            }
            if (!selfTest)
            {
                eventName = "Local\\HWP_AutoDocFit_Handoff_" + Guid.NewGuid().ToString("N");
                handoff = new EventWaitHandle(false, EventResetMode.ManualReset, eventName);
                start.EnvironmentVariables["DOCFIT_LAUNCHER_HANDOFF_EVENT"] = eventName;
                start.EnvironmentVariables["DOCFIT_LAUNCHER_MUTEX_NAME"] = mutexName;
            }
            process = Process.Start(start);
            if (process == null) throw new InvalidOperationException("앱 프로세스를 시작하지 못했습니다.");

            if (selfTest)
            {
                CloseSplash();
                process.WaitForExit();
                return process.ExitCode;
            }

            var timer = Stopwatch.StartNew();
            while (timer.ElapsedMilliseconds < 45000)
            {
                if (handoff.WaitOne(100))
                {
                    CloseSplash();
                    mutex.ReleaseMutex();
                    ownsMutex = false;
                    return 0;
                }
                if (process.HasExited)
                {
                    CloseSplash();
                    return process.ExitCode;
                }
            }
            throw new TimeoutException("앱이 시작 확인을 보내지 않아 실행을 중단했습니다.");
        }
        finally
        {
            if (handoff != null) handoff.Dispose();
            if (process != null) process.Dispose();
        }
    }

    private static bool CacheIsValid(string cachePath, PayloadManifest manifest)
    {
        string marker = Path.Combine(cachePath, ".docfit-complete");
        string appPath = Path.Combine(cachePath, "app_main.exe");
        try
        {
            if (!File.Exists(marker) || !File.Exists(appPath)) return false;
            if (!string.Equals(File.ReadAllText(marker, Encoding.UTF8).Trim(), manifest.PayloadHash,
                StringComparison.OrdinalIgnoreCase)) return false;
            foreach (ManifestItem item in manifest.Items)
            {
                string path = SafeCombine(cachePath, item.Path);
                var info = new FileInfo(path);
                if (!info.Exists || info.Length != item.Length) return false;
            }
            return manifest.Items.Any(i => string.Equals(i.Path, "app_main.exe", StringComparison.OrdinalIgnoreCase));
        }
        catch { return false; }
    }

    private static void ExtractPayload(string finalPath, PayloadManifest manifest, bool quiet)
    {
        string parent = Path.GetDirectoryName(finalPath);
        string staging = Path.Combine(parent, ".staging-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(staging);
        try
        {
            var expected = manifest.Items.ToDictionary(i => i.Path, StringComparer.OrdinalIgnoreCase);
            var written = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            using (Stream resource = Assembly.GetExecutingAssembly().GetManifestResourceStream(PayloadResource))
            using (var archive = new ZipArchive(resource, ZipArchiveMode.Read, false, Encoding.UTF8))
            {
                int count = archive.Entries.Count;
                int index = 0;
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    index++;
                    string relative = entry.FullName.Replace('\\', '/');
                    if (string.IsNullOrEmpty(relative) || relative.EndsWith("/", StringComparison.Ordinal))
                        throw new InvalidDataException("압축 파일에 빈 경로 또는 폴더 항목이 포함되어 있습니다.");
                    if (((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000)
                        throw new InvalidDataException("심볼릭 링크 항목은 안전을 위해 허용하지 않습니다.");
                    ManifestItem item;
                    if (!expected.TryGetValue(relative, out item) || !written.Add(relative))
                        throw new InvalidDataException("압축 파일의 항목이 매니페스트와 일치하지 않습니다.");

                    string outputPath = SafeCombine(staging, relative);
                    Directory.CreateDirectory(Path.GetDirectoryName(outputPath));
                    using (Stream input = entry.Open())
                    using (var output = new FileStream(outputPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    using (var sha = SHA256.Create())
                    {
                        byte[] buffer = new byte[1024 * 1024];
                        long total = 0;
                        int read;
                        while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                        {
                            total += read;
                            if (total > item.Length) throw new InvalidDataException("매니페스트보다 큰 파일입니다: " + relative);
                            sha.TransformBlock(buffer, 0, read, buffer, 0);
                            output.Write(buffer, 0, read);
                        }
                        sha.TransformFinalBlock(new byte[0], 0, 0);
                        string digest = BitConverter.ToString(sha.Hash).Replace("-", "").ToLowerInvariant();
                        if (total != item.Length || !string.Equals(digest, item.Sha256, StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException("압축 해제 검증에 실패했습니다: " + relative);
                    }
                    if (!quiet && splash != null)
                    {
                        splash.SetProgress(index, count, relative);
                    }
                }
            }
            if (written.Count != manifest.Items.Count) throw new InvalidDataException("압축 파일 일부 항목이 누락되었습니다.");
            File.WriteAllText(Path.Combine(staging, ".docfit-complete"), manifest.PayloadHash, new UTF8Encoding(false));
            ReplaceCache(staging, finalPath);
        }
        catch
        {
            try { if (Directory.Exists(staging)) Directory.Delete(staging, true); } catch { }
            throw;
        }
    }

    private static void ReplaceCache(string staging, string finalPath)
    {
        // 손상된 캐시는 바로 지우지 않는다: 잠깐 잡고 있는 프로세스(방금 끝난 자식·백신 검사)가 있으면
        // 삭제가 실패해 런처가 멈췄다(CI 실측). 옆으로 옮긴 뒤 새 폴더를 놓고, 옛 폴더는 나중에 지운다.
        string trash = null;
        for (int attempt = 0; ; attempt++)
        {
            try
            {
                if (Directory.Exists(finalPath))
                {
                    trash = Path.Combine(Path.GetDirectoryName(finalPath), ".trash-" + Guid.NewGuid().ToString("N"));
                    Directory.Move(finalPath, trash);
                }
                Directory.Move(staging, finalPath);
                break;
            }
            catch (IOException)
            {
                if (attempt >= 25) throw;
            }
            catch (UnauthorizedAccessException)
            {
                if (attempt >= 25) throw;
            }
            Thread.Sleep(200);
        }
        if (trash != null)
        {
            try { Directory.Delete(trash, true); } catch { }
        }
    }

    private static void CleanupOldCaches(string cacheRoot, string keepName)
    {
        Version currentVersion = CacheVersion(keepName);
        if (currentVersion == null) return;
        foreach (string path in Directory.GetDirectories(cacheRoot, "app_v*"))
        {
            if (string.Equals(Path.GetFileName(path), keepName, StringComparison.OrdinalIgnoreCase)) continue;
            Version candidateVersion = CacheVersion(Path.GetFileName(path));
            if (candidateVersion == null || candidateVersion > currentVersion) continue;
            if (CacheIsInUse(path)) continue;
            // Never recursively delete the published cache path: a failed move must leave it intact.
            string trash = Path.Combine(cacheRoot, ".trash-" + Guid.NewGuid().ToString("N"));
            try { Directory.Move(path, trash); }
            catch { continue; }
            try { Directory.Delete(trash, true); } catch { }
        }
        // 지우지 못하고 남은 옛 캐시(.trash-*)는 다음 실행 때 다시 지운다.
        foreach (string trash in Directory.GetDirectories(cacheRoot, ".trash-*"))
        {
            try { Directory.Delete(trash, true); } catch { }
        }
        // Another launcher may still be extracting into .staging-*; it owns that cleanup.
    }

    private static Version CacheVersion(string name)
    {
        if (!name.StartsWith("app_v", StringComparison.OrdinalIgnoreCase)) return null;
        int separator = name.LastIndexOf('_');
        if (separator <= 5) return null;
        string value = name.Substring(5, separator - 5);
        string numeric = new string(value.TakeWhile(c => char.IsDigit(c) || c == '.').ToArray());
        string[] parts = numeric.Split('.');
        if (parts.Length > 4) return null;
        Version version;
        return Version.TryParse(string.Join(".", parts.Concat(Enumerable.Repeat("0", 4 - parts.Length))),
            out version) ? version : null;
    }

    private static bool CacheIsInUse(string cachePath)
    {
        // The launcher exits after mutex handoff, so it cannot own an app-lifetime lock.
        try
        {
            string appPath = Path.GetFullPath(Path.Combine(cachePath, "app_main.exe"));
            bool inUse = false;
            foreach (Process process in Process.GetProcessesByName("app_main"))
            {
                using (process)
                {
                    try
                    {
                        if (string.Equals(Path.GetFullPath(process.MainModule.FileName), appPath,
                            StringComparison.OrdinalIgnoreCase)) inUse = true;
                    }
                    catch { inUse = true; } // Inaccessible processes are conservatively protected.
                }
            }
            if (inUse) return true;

            string pythonDll = Path.Combine(cachePath, "_internal", "python312.dll");
            IEnumerable<string> probes = Directory.GetFiles(cachePath, "*.pyd", SearchOption.AllDirectories);
            if (File.Exists(pythonDll)) probes = probes.Concat(new[] { pythonDll });
            foreach (string probe in probes)
            {
                using (var stream = new FileStream(probe, FileMode.Open, FileAccess.Write, FileShare.None)) { }
            }
            return false;
        }
        catch { return true; }
    }

    private static string SafeCombine(string root, string relative)
    {
        string normalized = relative.Replace('/', Path.DirectorySeparatorChar);
        string full = Path.GetFullPath(Path.Combine(root, normalized));
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!full.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("잘못된 압축 경로입니다.");
        return full;
    }

    private static string SafeVersion(string value)
    {
        foreach (char c in Path.GetInvalidFileNameChars()) value = value.Replace(c, '_');
        return value.Replace(' ', '_');
    }

    private static void ShowSplash(string version)
    {
        splash = new NativeSplash(version);
        Trace("splash-created");
        splash.Show();
        Trace("splash-shown");
    }

    private static void ReadManifestHeader(out string version, out string payloadHash)
    {
        version = null;
        payloadHash = null;
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(ManifestResource))
        {
            if (stream == null) throw new InvalidDataException("포터블 데이터 리소스를 찾지 못했습니다: " + ManifestResource);
            using (var reader = new StreamReader(stream, Encoding.UTF8, true))
            {
                string line;
                while ((version == null || payloadHash == null) && (line = reader.ReadLine()) != null)
                {
                    if (line.StartsWith("V\t", StringComparison.Ordinal)) version = line.Substring(2);
                    else if (line.StartsWith("P\t", StringComparison.Ordinal)) payloadHash = line.Substring(2);
                    else if (line.StartsWith("F\t", StringComparison.Ordinal)) break;
                }
            }
        }
        if (string.IsNullOrWhiteSpace(version) || payloadHash == null || payloadHash.Length != 64)
            throw new InvalidDataException("포터블 매니페스트가 올바르지 않습니다.");
    }

    private static PayloadManifest LoadManifest(string version, string payloadHash)
    {
        PayloadManifest manifest = PayloadManifest.Parse(ReadResourceText(ManifestResource));
        if (manifest.Version != version || manifest.PayloadHash != payloadHash)
            throw new InvalidDataException("포터블 매니페스트 머리글이 본문과 다릅니다.");
        return manifest;
    }

    private static string ReadResourceText(string name)
    {
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name))
        {
            if (stream == null) throw new InvalidDataException("포터블 데이터 리소스를 찾지 못했습니다: " + name);
            using (var reader = new StreamReader(stream, Encoding.UTF8, true)) return reader.ReadToEnd();
        }
    }

    private static string QuoteArgument(string value)
    {
        if (value.Length > 0 && value.All(c => !char.IsWhiteSpace(c) && c != '"')) return value;
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in value)
        {
            if (c == '\\') { slashes++; continue; }
            if (c == '"') result.Append('\\', slashes * 2 + 1);
            else result.Append('\\', slashes);
            result.Append(c);
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        result.Append('"');
        return result.ToString();
    }

    private static void ActivateExistingWindow()
    {
        EnumWindows(delegate(IntPtr hwnd, IntPtr unused)
        {
            if (!IsWindowVisible(hwnd)) return true;
            int length = GetWindowTextLength(hwnd);
            if (length <= 0) return true;
            var text = new StringBuilder(length + 1);
            GetWindowText(hwnd, text, text.Capacity);
            if (text.ToString().IndexOf("HWP_AutoDocFit", StringComparison.OrdinalIgnoreCase) >= 0 ||
                text.ToString().IndexOf("한글편집", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                ShowWindow(hwnd, SwRestore);
                SetForegroundWindow(hwnd);
                return false;
            }
            return true;
        }, IntPtr.Zero);
    }

    private static void CloseSplash()
    {
        if (splash == null) return;
        try { splash.Close(); } catch { }
        splash = null;
    }

    [DllImport("kernel32.dll")] private static extern bool AttachConsole(uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int MessageBoxW(IntPtr hwnd, string text, string caption, uint type);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowTextLength(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hwnd);
    private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);

    private sealed class PayloadManifest
    {
        public string Version;
        public string PayloadHash;
        public List<ManifestItem> Items = new List<ManifestItem>();

        public static PayloadManifest Parse(string text)
        {
            var result = new PayloadManifest();
            foreach (string line in text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] fields = line.Split(new[] { '\t' }, 4);
                if (fields[0] == "V" && fields.Length >= 2) result.Version = fields[1];
                else if (fields[0] == "P" && fields.Length >= 2) result.PayloadHash = fields[1];
                else if (fields[0] == "F" && fields.Length == 4)
                {
                    long size;
                    if (!long.TryParse(fields[2], NumberStyles.None, CultureInfo.InvariantCulture, out size) || size < 0)
                        throw new InvalidDataException("잘못된 파일 크기 매니페스트입니다.");
                    result.Items.Add(new ManifestItem { Sha256 = fields[1], Length = size, Path = fields[3] });
                }
            }
            if (string.IsNullOrWhiteSpace(result.Version) || result.PayloadHash == null || result.PayloadHash.Length != 64 || result.Items.Count == 0)
                throw new InvalidDataException("포터블 매니페스트가 올바르지 않습니다.");
            if (result.Items.Any(i => string.IsNullOrWhiteSpace(i.Path) || i.Path.Contains("\t") || i.Path.Contains("\n") || i.Path.Contains("\\")))
                throw new InvalidDataException("매니페스트에 허용되지 않는 경로가 포함되어 있습니다.");
            return result;
        }
    }

    private sealed class ManifestItem
    {
        public string Sha256;
        public long Length;
        public string Path;
    }

    // WinForms·System.Drawing을 불러오지 않는 Win32 창이다. 둘을 불러오고 창을 꾸미는 데만
    // 약 200ms가 들어 첫 실행 스플래시가 늦게 떴다(2.0.4 실측). 배경은 빌드 때 만든 BMP를 그대로 그린다.
    private sealed class NativeSplash
    {
        private const int Width = 500, Height = 260;
        private readonly WndProc proc;
        private readonly byte[] pixels;
        private BITMAPINFOHEADER header;
        private readonly string versionText;
        private string status = "최초 실행 자료를 준비하고 있습니다.";
        private int percent;
        private IntPtr hwnd, font;

        public NativeSplash(string version)
        {
            versionText = "HWP_AutoDocFit · v" + version;
            byte[] bmp;
            using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("DocFitSplash"))
            {
                if (stream == null) throw new InvalidDataException("스플래시 이미지 리소스를 찾지 못했습니다.");
                bmp = new byte[stream.Length];
                int offset = 0, read;
                while (offset < bmp.Length && (read = stream.Read(bmp, offset, bmp.Length - offset)) > 0) offset += read;
            }
            // 24비트 아래→위 BMP(빌드 스크립트가 resources/splash.png에서 만든다).
            if (bmp.Length < 54 || bmp[0] != (byte)'B' || bmp[1] != (byte)'M' || BitConverter.ToInt16(bmp, 28) != 24)
                throw new InvalidDataException("스플래시 이미지 형식이 올바르지 않습니다.");
            int dataOffset = BitConverter.ToInt32(bmp, 10);
            header = new BITMAPINFOHEADER
            {
                biSize = 40, biWidth = BitConverter.ToInt32(bmp, 18), biHeight = BitConverter.ToInt32(bmp, 22),
                biPlanes = 1, biBitCount = 24
            };
            pixels = new byte[bmp.Length - dataOffset];
            Buffer.BlockCopy(bmp, dataOffset, pixels, 0, pixels.Length);

            // 스플래시는 글자 입력이 없다. 첫 창에서 입력기(IME)를 준비하는 시간을 건너뛴다.
            try { ImmDisableIME(0); } catch { }
            proc = WindowProc;
            IntPtr instance = GetModuleHandleW(null);
            var cls = new WNDCLASSEXW
            {
                cbSize = Marshal.SizeOf(typeof(WNDCLASSEXW)), lpfnWndProc = Marshal.GetFunctionPointerForDelegate(proc),
                hInstance = instance, hCursor = LoadCursorW(IntPtr.Zero, (IntPtr)32512),
                hIcon = LoadIconW(instance, (IntPtr)32512), lpszClassName = "DocFitNativeSplash"
            };
            RegisterClassExW(ref cls);
            const uint style = 0x80000000 | 0x00800000; // WS_POPUP | WS_BORDER: 제목 줄을 그리지 않아 첫 표시가 빠르다
            const uint exStyle = 0x00000008 | 0x00040000; // WS_EX_TOPMOST | WS_EX_APPWINDOW(작업 표시줄)
            var rect = new RECT { Right = Width, Bottom = Height };
            AdjustWindowRectEx(ref rect, style, false, exStyle);
            int w = rect.Right - rect.Left, h = rect.Bottom - rect.Top;
            var work = new RECT();
            SystemParametersInfoW(0x0030, 0, ref work, 0); // SPI_GETWORKAREA
            hwnd = CreateWindowExW(exStyle, "DocFitNativeSplash", AppTitle + " - 실행 준비", style,
                work.Left + Math.Max(0, (work.Right - work.Left - w) / 2), work.Top + Math.Max(0, (work.Bottom - work.Top - h) / 2),
                w, h, IntPtr.Zero, IntPtr.Zero, instance, IntPtr.Zero);
            if (hwnd == IntPtr.Zero) throw new InvalidOperationException("스플래시 창을 만들지 못했습니다.");
        }

        public void Show()
        {
            ShowWindow(hwnd, 1);
            Trace("show");
            UpdateWindow(hwnd);
            Trace("paint");
            // 한글 글꼴을 처음 그리는 데 40ms쯤 걸리므로 배경 그림을 먼저 보이고 글은 다음 그리기에 넣는다.
            font = CreateFontW(-11, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, "Malgun Gothic");
            InvalidateRect(hwnd, IntPtr.Zero, false);
            UpdateWindow(hwnd);
            Trace("text");
            Pump();
        }

        public void SetProgress(int current, int total, string item)
        {
            percent = Math.Max(0, Math.Min(100, (int)((long)current * 100 / Math.Max(1, total))));
            status = "최초 실행 자료를 준비하고 있습니다. (" + current + "/" + total + ")";
            InvalidateRect(hwnd, IntPtr.Zero, false);
            Pump();
        }

        public void Close()
        {
            if (hwnd != IntPtr.Zero) { DestroyWindow(hwnd); hwnd = IntPtr.Zero; }
            if (font != IntPtr.Zero) { DeleteObject(font); font = IntPtr.Zero; }
            Pump();
        }

        private static void Pump()
        {
            MSG msg;
            while (PeekMessageW(out msg, IntPtr.Zero, 0, 0, 1))
            {
                TranslateMessage(ref msg);
                DispatchMessageW(ref msg);
            }
        }

        private IntPtr WindowProc(IntPtr window, uint message, IntPtr wParam, IntPtr lParam)
        {
            if (message == 0x0014) return (IntPtr)1; // WM_ERASEBKGND: 배경 그림이 덮는다
            if (message == 0x0010) return IntPtr.Zero; // WM_CLOSE: 압축 해제 중에는 닫지 않는다
            if (message == 0x000F) { Paint(window); return IntPtr.Zero; }
            return DefWindowProcW(window, message, wParam, lParam);
        }

        private void Paint(IntPtr window)
        {
            PAINTSTRUCT ps;
            IntPtr dc = BeginPaint(window, out ps);
            try
            {
                SetDIBitsToDevice(dc, 0, 0, (uint)header.biWidth, (uint)Math.Abs(header.biHeight), 0, 0, 0,
                    (uint)Math.Abs(header.biHeight), pixels, ref header, 0);
                // 배경 그림에는 바뀌는 글을 넣지 않는다(1.80.3 사용자 보고). 버전·진행·상태는 여기서만 그린다.
                if (font != IntPtr.Zero)
                {
                    IntPtr old = SelectObject(dc, font);
                    SetBkMode(dc, 1);
                    SetTextColor(dc, Rgb(83, 104, 145));
                    DrawLabel(dc, versionText, 119, 82, 340, 18);
                    DrawLabel(dc, status, 34, 194, 432, 20);
                    SelectObject(dc, old);
                }
                Fill(dc, 34, 170, 432, 8, Rgb(214, 220, 230));
                Fill(dc, 34, 170, 432 * percent / 100, 8, Rgb(37, 99, 235));
            }
            finally { EndPaint(window, ref ps); }
        }

        private static void DrawLabel(IntPtr dc, string text, int x, int y, int w, int h)
        {
            Fill(dc, x, y, w, h, Rgb(255, 255, 255));
            var rect = new RECT { Left = x, Top = y, Right = x + w, Bottom = y + h };
            DrawTextW(dc, text, -1, ref rect, 0x0004 | 0x0020 | 0x0800 | 0x8000); // VCENTER|SINGLELINE|NOPREFIX|END_ELLIPSIS
        }

        private static void Fill(IntPtr dc, int x, int y, int w, int h, uint color)
        {
            if (w <= 0) return;
            IntPtr brush = CreateSolidBrush(color);
            var rect = new RECT { Left = x, Top = y, Right = x + w, Bottom = y + h };
            FillRect(dc, ref rect, brush);
            DeleteObject(brush);
        }

        private static uint Rgb(int r, int g, int b) { return (uint)(r | (g << 8) | (b << 16)); }

        private delegate IntPtr WndProc(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct WNDCLASSEXW
        {
            public int cbSize; public uint style; public IntPtr lpfnWndProc; public int cbClsExtra; public int cbWndExtra;
            public IntPtr hInstance; public IntPtr hIcon; public IntPtr hCursor; public IntPtr hbrBackground;
            public string lpszMenuName; public string lpszClassName; public IntPtr hIconSm;
        }
        [StructLayout(LayoutKind.Sequential)] private struct RECT { public int Left, Top, Right, Bottom; }
        [StructLayout(LayoutKind.Sequential)] private struct POINT { public int X, Y; }
        [StructLayout(LayoutKind.Sequential)]
        private struct MSG { public IntPtr hwnd; public uint message; public IntPtr wParam, lParam; public uint time; public POINT pt; }
        [StructLayout(LayoutKind.Sequential)]
        private struct PAINTSTRUCT
        {
            public IntPtr hdc; public bool fErase; public RECT rcPaint; public bool fRestore, fIncUpdate;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 32)] public byte[] rgbReserved;
        }
        [StructLayout(LayoutKind.Sequential)]
        private struct BITMAPINFOHEADER
        {
            public int biSize, biWidth, biHeight; public short biPlanes, biBitCount;
            public int biCompression, biSizeImage, biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr GetModuleHandleW(string name);
        [DllImport("imm32.dll")] private static extern bool ImmDisableIME(uint threadId);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern ushort RegisterClassExW(ref WNDCLASSEXW cls);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr CreateWindowExW(uint exStyle, string className, string title, uint style, int x, int y, int w, int h, IntPtr parent, IntPtr menu, IntPtr instance, IntPtr param);
        [DllImport("user32.dll")] private static extern IntPtr DefWindowProcW(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")] private static extern bool AdjustWindowRectEx(ref RECT rect, uint style, bool menu, uint exStyle);
        [DllImport("user32.dll")] private static extern bool SystemParametersInfoW(uint action, uint param, ref RECT rect, uint winIni);
        [DllImport("user32.dll")] private static extern IntPtr LoadCursorW(IntPtr instance, IntPtr name);
        [DllImport("user32.dll")] private static extern IntPtr LoadIconW(IntPtr instance, IntPtr name);
        [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hwnd, int command);
        [DllImport("user32.dll")] private static extern bool UpdateWindow(IntPtr hwnd);
        [DllImport("user32.dll")] private static extern bool DestroyWindow(IntPtr hwnd);
        [DllImport("user32.dll")] private static extern bool InvalidateRect(IntPtr hwnd, IntPtr rect, bool erase);
        [DllImport("user32.dll")] private static extern bool PeekMessageW(out MSG msg, IntPtr hwnd, uint min, uint max, uint remove);
        [DllImport("user32.dll")] private static extern bool TranslateMessage(ref MSG msg);
        [DllImport("user32.dll")] private static extern IntPtr DispatchMessageW(ref MSG msg);
        [DllImport("user32.dll")] private static extern IntPtr BeginPaint(IntPtr hwnd, out PAINTSTRUCT ps);
        [DllImport("user32.dll")] private static extern bool EndPaint(IntPtr hwnd, ref PAINTSTRUCT ps);
        [DllImport("user32.dll")] private static extern int FillRect(IntPtr dc, ref RECT rect, IntPtr brush);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int DrawTextW(IntPtr dc, string text, int count, ref RECT rect, uint format);
        [DllImport("gdi32.dll")] private static extern int SetDIBitsToDevice(IntPtr dc, int x, int y, uint w, uint h, int sx, int sy, uint start, uint lines, byte[] bits, ref BITMAPINFOHEADER info, uint usage);
        [DllImport("gdi32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr CreateFontW(int height, int width, int escapement, int orientation, int weight, uint italic, uint underline, uint strike, uint charset, uint outPrecision, uint clipPrecision, uint quality, uint pitch, string face);
        [DllImport("gdi32.dll")] private static extern IntPtr SelectObject(IntPtr dc, IntPtr obj);
        [DllImport("gdi32.dll")] private static extern bool DeleteObject(IntPtr obj);
        [DllImport("gdi32.dll")] private static extern int SetBkMode(IntPtr dc, int mode);
        [DllImport("gdi32.dll")] private static extern uint SetTextColor(IntPtr dc, uint color);
        [DllImport("gdi32.dll")] private static extern IntPtr CreateSolidBrush(uint color);
    }
}
