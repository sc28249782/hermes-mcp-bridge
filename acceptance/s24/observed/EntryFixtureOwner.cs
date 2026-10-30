// CI fixture only: set the NEW test driver's default object owner to its own SID.
// No privilege/group/identity change, other-process access or runtime hook.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;
public static class EntryFixtureOwner {
    [StructLayout(LayoutKind.Sequential)] private struct Owner { public IntPtr Sid; }
    [DllImport("kernel32.dll")] private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    [DllImport("advapi32.dll", SetLastError=true)]
    private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError=true)]
    private static extern bool SetTokenInformation(IntPtr token, int kind, ref Owner owner, int length);
    public static void SetSelfDefaultOwner() {
        IntPtr token=IntPtr.Zero, sid=IntPtr.Zero;
        try {
            if (!OpenProcessToken(GetCurrentProcess(),0x88,out token))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            using (WindowsIdentity identity=WindowsIdentity.GetCurrent()) {
                byte[] raw=new byte[identity.User.BinaryLength];
                identity.User.GetBinaryForm(raw,0);
                sid=Marshal.AllocHGlobal(raw.Length); Marshal.Copy(raw,0,sid,raw.Length);
                Owner owner=new Owner { Sid=sid };
                if (!SetTokenInformation(token,4,ref owner,Marshal.SizeOf(typeof(Owner))))
                    throw new Win32Exception(Marshal.GetLastWin32Error());
            }
        } finally {
            if (sid!=IntPtr.Zero) Marshal.FreeHGlobal(sid);
            if (token!=IntPtr.Zero) CloseHandle(token);
        }
    }
}
