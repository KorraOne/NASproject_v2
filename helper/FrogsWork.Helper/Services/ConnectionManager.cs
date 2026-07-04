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
            DriveMapper.MapDrive(letter, mount.UncPath, session.Username, session.Password, persist: true);
            _mappedLetters.Add(letter);
        }

        SessionStore.Save(session);
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
