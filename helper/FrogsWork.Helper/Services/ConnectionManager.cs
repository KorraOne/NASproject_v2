using System.ComponentModel;
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
        var mappedThisSession = new List<char>();
        try
        {
            foreach (var mount in mounts.Mounts)
            {
                var suggested = mount.SuggestedLetter.Length > 0 ? mount.SuggestedLetter[0] : 'U';
                var letter = DriveMapper.ResolveLetter(suggested, reserved);
                reserved.Add(letter);
                var uncPath = ResolveUncPath(mount.UncPath, session.Host);
                try
                {
                    DriveMapper.MapDrive(letter, uncPath, session.Username, session.Password, persist: true);
                }
                catch (Win32Exception ex)
                {
                    throw new InvalidOperationException(
                        $"Could not map {mount.Label} ({uncPath}): {ex.Message}",
                        ex);
                }

                mappedThisSession.Add(letter);
                _mappedLetters.Add(letter);
            }

            SessionStore.Save(session);
        }
        catch
        {
            foreach (var letter in mappedThisSession)
            {
                try
                {
                    DriveMapper.Disconnect(letter);
                }
                catch
                {
                    // ignore rollback errors
                }
            }

            _mappedLetters.Clear();
            throw;
        }
    }

    private static string ResolveUncPath(string uncPath, string host)
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

        return $@"\\{host}\{parts[1]}";
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
