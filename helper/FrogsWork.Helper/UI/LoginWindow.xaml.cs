using System.Windows;
using System.Windows.Input;
using FrogsWork.Helper.Discovery;
using FrogsWork.Helper.Services;

namespace FrogsWork.Helper.UI;

public partial class LoginWindow : Window
{
    public UserSession? Session { get; private set; }

    public LoginWindow()
    {
        InitializeComponent();
        HostBox.Text = ApplianceDiscovery.DefaultHost;
        Loaded += OnLoaded;
    }

    public void Prefill(UserSession session)
    {
        HostBox.Text = session.Host;
        UsernameBox.Text = session.Username;
        PasswordBox.Password = session.Password;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        try
        {
            HostBox.Items.Clear();
            HostBox.Items.Add(ApplianceDiscovery.DefaultHost);
            var appliances = await ApplianceDiscovery.DiscoverAsync();
            foreach (var appliance in appliances)
            {
                if (!HostBox.Items.Contains(appliance.Hostname))
                {
                    HostBox.Items.Add(appliance.Hostname);
                }
            }
            if (HostBox.Items.Count > 0 && string.IsNullOrWhiteSpace(HostBox.Text))
            {
                HostBox.Text = appliances[0].Hostname;
            }
        }
        catch
        {
            // Keep default host if discovery fails.
        }
    }

    private async void Connect_Click(object sender, RoutedEventArgs e)
    {
        ErrorText.Text = "";
        ErrorPanel.Visibility = Visibility.Collapsed;
        ConnectButton.IsEnabled = false;
        Mouse.OverrideCursor = System.Windows.Input.Cursors.Wait;
        try
        {
            var host = HostBox.Text.Trim();
            var username = UsernameBox.Text.Trim().ToLowerInvariant();
            var password = PasswordBox.Password;
            if (string.IsNullOrWhiteSpace(host) || string.IsNullOrWhiteSpace(username) || string.IsNullOrEmpty(password))
            {
                ErrorText.Text = "Enter the address, username, and password.";
                ErrorPanel.Visibility = Visibility.Visible;
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
            ErrorPanel.Visibility = Visibility.Visible;
            Session = null;
        }
        finally
        {
            Mouse.OverrideCursor = null;
            ConnectButton.IsEnabled = true;
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
