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
using System.Windows.Forms;

internal static class SmartLauncher
{
    private const string AppTitle = "한글편집 후처리 (HWP_AutoDocFit)";
    private const string PayloadResource = "DocFitPayload";
    private const string ManifestResource = "DocFitManifest";
    private const string MutexSuffix = "HWP_AutoDocFit_SingleInstance_Mutex";
    private const int SwRestore = 9;
    private static SplashForm splash;

    [STAThread]
    private static int Main(string[] args)
    {
        bool selfTest = args.Any(a => string.Equals(a, "--self-test", StringComparison.OrdinalIgnoreCase));
        string mutexName = null;
        Mutex mutex = null;
        bool ownsMutex = false;
        string cachePath = null;

        try
        {
            string manifestText = ReadResourceText(ManifestResource);
            PayloadManifest manifest = PayloadManifest.Parse(manifestText);
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string cacheRoot = Path.Combine(localAppData, "HWP_AutoDocFit");
            Directory.CreateDirectory(cacheRoot);
            cachePath = Path.Combine(cacheRoot, "app_v" + SafeVersion(manifest.Version) + "_" + manifest.PayloadHash.Substring(0, 12));

            if (!selfTest)
            {
                mutexName = "Global\\" + MutexSuffix;
                try
                {
                    mutex = new Mutex(true, mutexName, out ownsMutex);
                }
                catch
                {
                    mutexName = "Local\\" + MutexSuffix;
                    mutex = new Mutex(true, mutexName, out ownsMutex);
                }
                if (!ownsMutex)
                {
                    mutex.Dispose();
                    ActivateExistingWindow();
                    return 0;
                }
            }

            if (!CacheIsValid(cachePath, manifest))
            {
                if (!selfTest)
                {
                    Application.EnableVisualStyles();
                    splash = new SplashForm();
                    splash.Show();
                    Application.DoEvents();
                }
                ExtractPayload(cachePath, manifest, selfTest);
            }

            string appPath = Path.Combine(cachePath, "app_main.exe");
            int exitCode = StartApplication(appPath, cachePath, args, selfTest, mutex, mutexName, ref ownsMutex);
            mutex = null;
            if (!selfTest) CleanupOldCaches(cacheRoot, Path.GetFileName(cachePath));
            return exitCode;
        }
        catch (Exception ex)
        {
            CloseSplash();
            if (!args.Any(a => string.Equals(a, "--self-test", StringComparison.OrdinalIgnoreCase)))
            {
                MessageBox.Show("앱 실행 준비 중 오류가 발생했습니다.\r\n\r\n" + ex.Message, AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
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
                WorkingDirectory = cachePath,
                UseShellExecute = false,
                Arguments = string.Join(" ", args.Select(QuoteArgument).ToArray())
            };
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
        if (Directory.Exists(finalPath)) Directory.Delete(finalPath, true);
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
                        Application.DoEvents();
                    }
                }
            }
            if (written.Count != manifest.Items.Count) throw new InvalidDataException("압축 파일 일부 항목이 누락되었습니다.");
            File.WriteAllText(Path.Combine(staging, ".docfit-complete"), manifest.PayloadHash, new UTF8Encoding(false));
            Directory.Move(staging, finalPath);
        }
        catch
        {
            try { if (Directory.Exists(staging)) Directory.Delete(staging, true); } catch { }
            throw;
        }
    }

    private static void CleanupOldCaches(string cacheRoot, string keepName)
    {
        foreach (string path in Directory.GetDirectories(cacheRoot, "app_v*"))
        {
            if (string.Equals(Path.GetFileName(path), keepName, StringComparison.OrdinalIgnoreCase)) continue;
            try { Directory.Delete(path, true); } catch { }
        }
        foreach (string path in Directory.GetDirectories(cacheRoot, ".staging-*"))
        {
            try { Directory.Delete(path, true); } catch { }
        }
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
        try { splash.Close(); splash.Dispose(); } catch { }
        splash = null;
    }

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

    private sealed class SplashForm : Form
    {
        private readonly Label label;
        private readonly ProgressBar bar;

        public SplashForm()
        {
            Text = AppTitle + " - 실행 준비";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterScreen;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = true;
            TopMost = true;
            Width = 440;
            Height = 138;
            label = new Label { Left = 22, Top = 20, Width = 380, Height = 32, Text = "최초 실행 자료를 준비하고 있습니다." };
            bar = new ProgressBar { Left = 22, Top = 62, Width = 380, Height = 20, Minimum = 0, Maximum = 100 };
            Controls.Add(label);
            Controls.Add(bar);
        }

        public void SetProgress(int current, int total, string item)
        {
            bar.Value = Math.Max(0, Math.Min(100, (int)((long)current * 100 / Math.Max(1, total))));
            label.Text = "최초 실행 자료를 준비하고 있습니다. (" + current + "/" + total + ")";
        }
    }
}
