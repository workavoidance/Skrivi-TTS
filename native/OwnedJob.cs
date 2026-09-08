using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
namespace Reader.Windows
{
    // Windows closes this handle on a crash as well as normal exit, terminating our runtime only.
    internal sealed class OwnedJob : IDisposable
    {
        IntPtr handle;
        [StructLayout(LayoutKind.Sequential)] struct Basic { public long PerProcess, PerJob; public uint Flags; public UIntPtr Min, Max; public uint Active; public UIntPtr Affinity; public uint Priority, Scheduling; }
        [StructLayout(LayoutKind.Sequential)] struct Io { public ulong A, B, C, D, E, F; }
        [StructLayout(LayoutKind.Sequential)] struct Extended { public Basic Basic; public Io Io; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob; }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attrs, string name);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetInformationJobObject(IntPtr h, int cls, ref Extended info, int size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
        public OwnedJob(Process process)
        {
            handle = CreateJobObject(IntPtr.Zero, null);
            var info = new Extended(); info.Basic.Flags = 0x2000;
            if (handle == IntPtr.Zero || !SetInformationJobObject(handle, 9, ref info, Marshal.SizeOf(info)) || !AssignProcessToJobObject(handle, process.Handle))
            { Dispose(); throw new InvalidOperationException("Windows could not establish safe runtime cleanup."); }
        }
        public void Dispose() { if (handle != IntPtr.Zero) { CloseHandle(handle); handle = IntPtr.Zero; } }
    }
}
