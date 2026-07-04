using System.Net;
using System.Net.Sockets;
using FrogsWork.Helper.Api;
using FrogsWork.Helper.DriveMapping;

namespace FrogsWork.Helper.Services;

public sealed class ConnectionManager
{
    public static ConnectionManager Instance { get; } = new();

    private readonly List<char> _mappedLetters = [];

    public IReadOnlyList<char> MappedLetters => _mappedLetters;

    public async Task ConnectAsync(UserSession session, CancellationToken cancellationToken = default)
    {
        DisconnectAll();

        using var api = new HelperApiClient(session.ApplianceUrl, session.Username, session.Password);
        var mounts = await api.GetMountsAsync(session.Host, cancellationToken);

        var reserved = new HashSet<char>();
        foreach (var mount in mounts.Mounts)
        {
            var suggested = mount.SuggestedLetter.Length > 0 ? mount.SuggestedLetter[0] : 'U';
            var letter = DriveMapper.ResolveLetter(suggested, reserved);
            reserved.Add(letter);
            var uncPath = ResolveUncPath(mount.UncPath, session.Host);
            DriveMapper.MapDrive(letter, uncPath, session.Username, session.Password, persist: true);
            _mappedLetters.Add(letter);
        }

        SessionStore.Save(session);
    }

    private static string ResolveUncPath(string uncPath, string fallbackHost)
    {
        if (!uncPath.StartsWith(@"\\", StringComparison.Ordinal))
        {
            return uncPath;
        }

        var parts = uncPath.Split('\\', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length < 2)
        {
            return uncPath;
        }

        var host = parts[0];
        var share = parts[1];
        try
        {
            var addresses = Dns.GetHostAddresses(host);
            var ip = addresses.FirstOrDefault(a => a.AddressFamily == AddressFamily.InterNetwork);
            if (ip is not null)
            {
                return $@"\\{ip}\{share}";
            }
        }
        catch
        {
            // fall through
        }

        if (IPAddress.TryParse(fallbackHost, out _))
        {
            return $@"\\{fallbackHost}\{share}";
        }

        return uncPath;
    }

    public void DisconnectAll()
    {
        foreach (var letter in _mappedLetters.ToList())
        {
            try
            {
                DriveMapper.Disconnect(letter);
            }
            catch
            {
                // ignore disconnect errors
            }
        }
        _mappedLetters.Clear();
    }
}
