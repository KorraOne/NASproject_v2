using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace FrogsWork.Helper.DriveMapping;

internal static class NativeMethods
{
    public const int ResourceGlobalNet = 0x00000002;
    public const int ConnectUpdateProfile = 0x00000001;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct NetResource
    {
        public int Scope;
        public int ResourceType;
        public int DisplayType;
        public int Usage;
        public string LocalName;
        public string RemoteName;
        public string Comment;
        public string Provider;
    }

    [DllImport("mpr.dll", CharSet = CharSet.Unicode)]
    public static extern int WNetAddConnection2(
        ref NetResource netResource,
        string password,
        string username,
        int flags);

    [DllImport("mpr.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern int WNetCancelConnection2(string name, int flags, bool force);
}

public static class DriveMapper
{
    private const int ResourcetypeDisk = 0x00000001;

    public static void MapDrive(char letter, string uncPath, string username, string password, bool persist = true)
    {
        var localName = $"{letter}:";
        var resource = new NativeMethods.NetResource
        {
            Scope = NativeMethods.ResourceGlobalNet,
            ResourceType = ResourcetypeDisk,
            LocalName = localName,
            RemoteName = uncPath,
        };

        var flags = persist ? NativeMethods.ConnectUpdateProfile : 0;
        var result = NativeMethods.WNetAddConnection2(ref resource, password, username, flags);
        if (result != 0)
        {
            throw new Win32Exception(result);
        }
    }

    public static void Disconnect(char letter, bool force = true)
    {
        var localName = $"{letter}:";
        NativeMethods.WNetCancelConnection2(localName, 0, force);
    }

    public static bool IsLetterAvailable(char letter)
    {
        return !DriveInfo.GetDrives().Any(d =>
            d.Name.StartsWith($"{letter}:", StringComparison.OrdinalIgnoreCase));
    }

    public static char ResolveLetter(char suggested, ISet<char> reserved)
    {
        if (IsUsable(suggested, reserved))
        {
            return char.ToUpperInvariant(suggested);
        }

        foreach (var candidate in "STUVWXYZQRPNMLKJIHGFEDC")
        {
            if (IsUsable(candidate, reserved))
            {
                return candidate;
            }
        }

        throw new InvalidOperationException("No drive letters are available.");
    }

    private static bool IsUsable(char letter, ISet<char> reserved)
    {
        letter = char.ToUpperInvariant(letter);
        if (letter is < 'D' or > 'Z')
        {
            return false;
        }
        return !reserved.Contains(letter) && IsLetterAvailable(letter);
    }
}
