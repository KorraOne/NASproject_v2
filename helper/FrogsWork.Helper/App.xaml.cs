using System.Windows;
using FrogsWork.Helper.Services;
using FrogsWork.Helper.UI;

namespace FrogsWork.Helper;

public partial class App : System.Windows.Application
{
    private TrayController? _tray;

    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        _tray = new TrayController();
        _tray.ConnectRequested += (_, _) => ShowLogin();
        _tray.DisconnectRequested += (_, _) => ConnectionManager.Instance.DisconnectAll();
        _tray.ExitRequested += (_, _) => ShutdownApp();

        if (SessionStore.TryLoad(out var session))
        {
            try
            {
                await ConnectionManager.Instance.ConnectAsync(session);
                _tray.SetStatus("Connected to FrogsWork");
                return;
            }
            catch
            {
                SessionStore.Clear();
            }
        }

        ShowLogin();
    }

    private void ShowLogin()
    {
        var login = new LoginWindow();
        if (login.ShowDialog() == true && login.Session is not null)
        {
            _tray?.SetStatus($"Connected as {login.Session.Username}");
        }
    }

    private void ShutdownApp()
    {
        _tray?.Dispose();
        Shutdown();
    }
}
