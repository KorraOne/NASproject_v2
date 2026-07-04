using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace FrogsWork.Helper.Services;

public sealed record UserSession(string ApplianceUrl, string Host, string Username, string Password);

public static class SessionStore
{
    private static readonly string StorePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "FrogsWork",
        "session.json");

    public static void Save(UserSession session)
    {
        var directory = Path.GetDirectoryName(StorePath)!;
        Directory.CreateDirectory(directory);
        var protectedPassword = ProtectedData.Protect(
            Encoding.UTF8.GetBytes(session.Password),
            optionalEntropy: null,
            scope: DataProtectionScope.CurrentUser);
        var payload = new StoredSession(
            session.ApplianceUrl,
            session.Host,
            session.Username,
            Convert.ToBase64String(protectedPassword));
        File.WriteAllText(StorePath, JsonSerializer.Serialize(payload));
    }

    public static bool TryLoad(out UserSession session)
    {
        session = null!;
        if (!File.Exists(StorePath))
        {
            return false;
        }

        var payload = JsonSerializer.Deserialize<StoredSession>(File.ReadAllText(StorePath));
        if (payload is null)
        {
            return false;
        }

        var passwordBytes = ProtectedData.Unprotect(
            Convert.FromBase64String(payload.ProtectedPassword),
            optionalEntropy: null,
            scope: DataProtectionScope.CurrentUser);
        session = new UserSession(
            payload.ApplianceUrl,
            payload.Host,
            payload.Username,
            Encoding.UTF8.GetString(passwordBytes));
        return true;
    }

    public static void Clear()
    {
        if (File.Exists(StorePath))
        {
            File.Delete(StorePath);
        }
    }

    private sealed record StoredSession(
        string ApplianceUrl,
        string Host,
        string Username,
        string ProtectedPassword);
}
