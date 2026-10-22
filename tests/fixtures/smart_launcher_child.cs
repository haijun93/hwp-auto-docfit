using System;
using System.IO;
using System.Text;
using System.Threading;

internal static class SmartLauncherTestChild
{
    private static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "convert")
        {
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_PATH"))) return 12;
            if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_HANDOFF_EVENT"))) return 13;
            File.WriteAllText(args[1], Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_PATH"), new UTF8Encoding(false));
            return 7;
        }
        if (args.Length == 4 && args[0] == "--self-test" && args[1] == "--self-test-report" &&
            args[3] == "argument with spaces")
        {
            File.WriteAllText(args[2], "{\"ok\":true}", new UTF8Encoding(false));
            return 0;
        }

        if (args.Length == 2 && args[0] == "--handoff-report")
        {
            string mutexName = Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_MUTEX_NAME");
            string eventName = Environment.GetEnvironmentVariable("DOCFIT_LAUNCHER_HANDOFF_EVENT");
            if (string.IsNullOrEmpty(mutexName) || string.IsNullOrEmpty(eventName)) return 9;
            bool createdNew;
            using (var mutex = new Mutex(true, mutexName, out createdNew))
            {
                if (createdNew) return 10;
                using (EventWaitHandle handoff = EventWaitHandle.OpenExisting(eventName)) handoff.Set();
                if (!mutex.WaitOne(30000)) return 11;
                File.WriteAllText(args[1], "{\"handoff\":true}", new UTF8Encoding(false));
                Thread.Sleep(1000);
            }
            return 0;
        }
        return 8;
    }
}
