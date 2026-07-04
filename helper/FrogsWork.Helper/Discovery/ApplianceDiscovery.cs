using Zeroconf;

namespace FrogsWork.Helper.Discovery;

public sealed record DiscoveredAppliance(string DisplayName, string Hostname, int Port);

public static class ApplianceDiscovery
{
    public const string DefaultHost = "frogswork.local";
    private const string ServiceType = "_frogswork._tcp.local.";

    public static async Task<IReadOnlyList<DiscoveredAppliance>> DiscoverAsync(
        CancellationToken cancellationToken = default)
    {
        try
        {
            var hosts = await ZeroconfResolver.ResolveAsync(
                ServiceType,
                TimeSpan.FromSeconds(4),
                cancellationToken: cancellationToken);

            var results = new List<DiscoveredAppliance>();
            foreach (var host in hosts)
            {
                foreach (var service in host.Services.Values)
                {
                    var hostname = host.DisplayName;
                    if (hostname.EndsWith(".local", StringComparison.OrdinalIgnoreCase))
                    {
                        hostname = hostname[..^6];
                    }

                    results.Add(new DiscoveredAppliance(
                        DisplayName: host.DisplayName,
                        Hostname: hostname,
                        Port: service.Port));
                }
            }

            if (results.Count > 0)
            {
                return results;
            }
        }
        catch
        {
            // fall through to default host
        }

        return [new DiscoveredAppliance("FrogsWork (manual)", DefaultHost, 80)];
    }
}
