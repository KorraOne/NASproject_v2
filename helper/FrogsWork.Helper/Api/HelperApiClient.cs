using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json.Serialization;

namespace FrogsWork.Helper.Api;

public sealed class HelperApiClient : IDisposable
{
    private readonly HttpClient _http;

    public HelperApiClient(string applianceBaseUrl, string username, string password)
    {
        _http = new HttpClient
        {
            BaseAddress = new Uri(applianceBaseUrl.TrimEnd('/') + "/"),
            Timeout = TimeSpan.FromSeconds(15),
        };
        var token = Convert.ToBase64String(Encoding.UTF8.GetBytes($"{username}:{password}"));
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", token);
    }

    public async Task<MountListResponse> GetMountsAsync(string host, CancellationToken cancellationToken = default)
    {
        var url = $"api/helper/mounts?host={Uri.EscapeDataString(host)}";
        var response = await _http.GetAsync(url, cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            var detail = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new InvalidOperationException(ParseDetail(detail) ?? "Could not load drive list from FrogsWork.");
        }

        var payload = await response.Content.ReadFromJsonAsync<MountListDto>(cancellationToken);
        return payload?.ToPublic() ?? throw new InvalidOperationException("Empty response from FrogsWork.");
    }

    private static string? ParseDetail(string body)
    {
        try
        {
            using var doc = System.Text.Json.JsonDocument.Parse(body);
            if (doc.RootElement.TryGetProperty("detail", out var detail))
            {
                return detail.GetString();
            }
        }
        catch
        {
            // ignore parse errors
        }
        return null;
    }

    public void Dispose() => _http.Dispose();
}

internal sealed class MountListDto
{
    [JsonPropertyName("hostname")]
    public string Hostname { get; set; } = "";

    [JsonPropertyName("username")]
    public string Username { get; set; } = "";

    [JsonPropertyName("display_name")]
    public string DisplayName { get; set; } = "";

    [JsonPropertyName("mounts")]
    public List<MountInfoDto> Mounts { get; set; } = [];

    public MountListResponse ToPublic() => new()
    {
        Hostname = Hostname,
        Username = Username,
        DisplayName = DisplayName,
        Mounts = Mounts.Select(m => m.ToPublic()).ToList(),
    };
}

internal sealed class MountInfoDto
{
    [JsonPropertyName("label")]
    public string Label { get; set; } = "";

    [JsonPropertyName("share")]
    public string Share { get; set; } = "";

    [JsonPropertyName("unc_path")]
    public string UncPath { get; set; } = "";

    [JsonPropertyName("suggested_letter")]
    public string SuggestedLetter { get; set; } = "";

    [JsonPropertyName("kind")]
    public string Kind { get; set; } = "";

    [JsonPropertyName("access")]
    public string Access { get; set; } = "";

    public MountInfo ToPublic() => new()
    {
        Label = Label,
        Share = Share,
        UncPath = UncPath,
        SuggestedLetter = SuggestedLetter,
        Kind = Kind,
        Access = Access,
    };
}
