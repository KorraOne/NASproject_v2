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
        _tray.DisconnectRequested += (_, _) => ConnectionManager.Instance.DisconnectAll();
        _tray.ExitRequested += (_, _) => ShutdownApp();

        if (!ShowLogin())
        {
            ShutdownApp();
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
                "FrogsWork Helper",
                Forms.MessageBoxButtons.OK,
                Forms.MessageBoxIcon.Error);
            args.Handled = true;
        };

        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            var message = args.ExceptionObject is Exception ex ? ex.Message : "Unknown error.";
            Forms.MessageBox.Show(
                message,
                "FrogsWork Helper",
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
