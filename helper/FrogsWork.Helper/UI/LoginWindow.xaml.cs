using System.Windows;
using FrogsWork.Helper.Discovery;
using FrogsWork.Helper.Services;

namespace FrogsWork.Helper.UI;

public partial class LoginWindow : Window
{
    public UserSession? Session { get; private set; }

    public LoginWindow()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        HostBox.Items.Clear();
        var appliances = await ApplianceDiscovery.DiscoverAsync();
        foreach (var appliance in appliances)
        {
            HostBox.Items.Add(appliance.Hostname);
        }
        HostBox.Text = appliances[0].Hostname;
    }

    private async void Connect_Click(object sender, RoutedEventArgs e)
    {
        ErrorText.Text = "";
        ConnectButton.IsEnabled = false;
        try
        {
            var host = HostBox.Text.Trim();
            var username = UsernameBox.Text.Trim().ToLowerInvariant();
            var password = PasswordBox.Password;
            if (string.IsNullOrWhiteSpace(host) || string.IsNullOrWhiteSpace(username) || string.IsNullOrEmpty(password))
            {
                ErrorText.Text = "Enter appliance, username, and password.";
                return;
            }

            var applianceUrl = host.Contains("://", StringComparison.Ordinal)
                ? host
                : $"http://{host}";

            Session = new UserSession(applianceUrl, host, username, password);
            await ConnectionManager.Instance.ConnectAsync(Session);
            DialogResult = true;
            Close();
        }
        catch (Exception ex)
        {
            ErrorText.Text = ex.Message;
            Session = null;
        }
        finally
        {
            ConnectButton.IsEnabled = true;
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
