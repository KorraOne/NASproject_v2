using System.Windows;
using FrogsWork.Helper.Services;
using FrogsWork.Helper.UI;
using Forms = System.Windows.Forms;

namespace FrogsWork.Helper;

public partial class App : System.Windows.Application
{
    private TrayController? _tray;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        RegisterExceptionHandlers();

        _tray = new TrayController();
        _tray.ConnectRequested += (_, _) => ShowLogin();
        _tray.RefreshRequested += (_, _) => _ = RefreshFromSavedSessionAsync();
        _tray.DisconnectRequested += (_, _) => ConnectionManager.Instance.DisconnectAll();
        _tray.ExitRequested += (_, _) => ShutdownApp();

        if (SessionStore.TryLoad(out var saved))
        {
            _tray.SetStatus($"Reconnecting as {saved.Username}…");
            _ = AutoConnectAsync(saved);
        }
        else if (!ShowLogin())
        {
            ShutdownApp();
        }
    }

    private async Task AutoConnectAsync(UserSession session)
    {
        try
        {
            await ConnectionManager.Instance.ConnectAsync(session);
            _tray?.SetStatus($"Connected as {session.Username}");
        }
        catch (Exception ex)
        {
            _tray?.SetStatus("Could not reconnect — use Connect…");
            Forms.MessageBox.Show(
                ex.Message,
                "FrogsWork File Storage",
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Warning);
            if (!ShowLogin())
            {
                ShutdownApp();
            }
        }
    }

    private async Task RefreshFromSavedSessionAsync()
    {
        if (!SessionStore.TryLoad(out var session))
        {
            ShowLogin();
            return;
        }

        try
        {
            await ConnectionManager.Instance.ConnectAsync(session);
            _tray?.SetStatus($"Refreshed folders for {session.Username}");
        }
        catch (Exception ex)
        {
            Forms.MessageBox.Show(
                ex.Message,
                "FrogsWork File Storage",
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Error);
        }
    }

    private bool ShowLogin()
    {
        var login = new LoginWindow();
        if (SessionStore.TryLoad(out var session))
        {
            login.Prefill(session);
        }

        if (login.ShowDialog() != true || login.Session is null)
        {
            return false;
        }

        _tray?.SetStatus($"Connected as {login.Session.Username}");
        return true;
    }

    private void RegisterExceptionHandlers()
    {
        DispatcherUnhandledException += (_, args) =>
        {
            Forms.MessageBox.Show(
                args.Exception.Message,
                "FrogsWork File Storage",
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Error);
            args.Handled = true;
        };

        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            var message = args.ExceptionObject is Exception ex ? ex.Message : "Unknown error.";
            Forms.MessageBox.Show(
                message,
                "FrogsWork File Storage",
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Error);
        };
    }

    private void ShutdownApp()
    {
        _tray?.Dispose();
        Shutdown();
    }
}
