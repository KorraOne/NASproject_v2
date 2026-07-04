using System.Drawing;
using FrogsWork.Helper.Services;
using Forms = System.Windows.Forms;

namespace FrogsWork.Helper.UI;

public sealed class TrayController : IDisposable
{
    private readonly Forms.NotifyIcon _icon;

    public event EventHandler? ConnectRequested;
    public event EventHandler? DisconnectRequested;
    public event EventHandler? ExitRequested;

    public TrayController()
    {
        _icon = new Forms.NotifyIcon
        {
            Icon = SystemIcons.Application,
            Visible = true,
            Text = "FrogsWork File Storage",
        };

        var menu = new Forms.ContextMenuStrip();
        menu.Items.Add("Connect…", null, (_, _) => ConnectRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add("Disconnect drives", null, (_, _) => DisconnectRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add(new Forms.ToolStripSeparator());
        menu.Items.Add("Exit", null, (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty));
        _icon.ContextMenuStrip = menu;
        _icon.DoubleClick += (_, _) => ConnectRequested?.Invoke(this, EventArgs.Empty);
    }

    public void SetStatus(string text)
    {
        _icon.Text = text.Length > 63 ? text[..63] : text;
        _icon.ShowBalloonTip(
            3000,
            "FrogsWork",
            text,
            Forms.ToolTipIcon.Info);
    }

    public void Dispose()
    {
        _icon.Visible = false;
        _icon.Dispose();
    }
}
