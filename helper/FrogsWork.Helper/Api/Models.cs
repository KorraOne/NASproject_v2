namespace FrogsWork.Helper.Api;

public sealed class MountListResponse
{
    public string Hostname { get; set; } = "";
    public string Username { get; set; } = "";
    public string DisplayName { get; set; } = "";
    public List<MountInfo> Mounts { get; set; } = [];
}

public sealed class MountInfo
{
    public string Label { get; set; } = "";
    public string Share { get; set; } = "";
    public string UncPath { get; set; } = "";
    public string SuggestedLetter { get; set; } = "";
    public string Kind { get; set; } = "";
    public string Access { get; set; } = "";
}
