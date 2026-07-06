using System.Drawing;
using System.Runtime.InteropServices;
using FrogsWork.Helper.Services;
using Forms = System.Windows.Forms;

namespace FrogsWork.Helper.UI;

public sealed class TrayController : IDisposable
{
    private readonly Forms.NotifyIcon _icon;

    public event EventHandler? ConnectRequested;
    public event EventHandler? RefreshRequested;
    public event EventHandler? DisconnectRequested;
    public event EventHandler? ExitRequested;

    public TrayController()
    {
        _icon = new Forms.NotifyIcon
        {
            Icon = LoadTrayIcon(),
            Visible = true,
            Text = "FrogsWork File Storage",
        };

        var menu = new Forms.ContextMenuStrip();
        menu.Items.Add("Connect…", null, (_, _) => ConnectRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add("Refresh folders", null, (_, _) => RefreshRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add("Disconnect drives", null, (_, _) => DisconnectRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add(new Forms.ToolStripSeparator());
        menu.Items.Add("Exit", null, (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty));
        _icon.ContextMenuStrip = menu;
        _icon.DoubleClick += (_, _) => ConnectRequested?.Invoke(this, EventArgs.Empty);
    }

    private static Icon LoadTrayIcon()
    {
        foreach (var loader in new Func<Icon?>[]
        {
            LoadIconFromPackUri,
            LoadIconFromOutputAssets,
            LoadIconFromLogoPng,
        })
        {
            var icon = loader();
            if (icon is not null)
            {
                return icon;
            }
        }

        return SystemIcons.Application;
    }

    private static Icon? LoadIconFromPackUri()
    {
        try
        {
            var stream = System.Windows.Application.GetResourceStream(
                new Uri("pack://application:,,,/Assets/app.ico"))?.Stream;
            if (stream is null)
            {
                return null;
            }

            using (stream)
            {
                return new Icon(stream);
            }
        }
        catch
        {
            return null;
        }
    }

    private static Icon? LoadIconFromOutputAssets()
    {
        var path = System.IO.Path.Combine(AppContext.BaseDirectory, "Assets", "app.ico");
        return System.IO.File.Exists(path) ? new Icon(path) : null;
    }

    private static Icon? LoadIconFromLogoPng()
    {
        try
        {
            var bitmap = LoadLogoBitmap();
            if (bitmap is null)
            {
                return null;
            }

            using (bitmap)
            using (var resized = new Bitmap(bitmap, new Size(32, 32)))
            {
                return CreateIconFromBitmap(resized);
            }
        }
        catch
        {
            return null;
        }
    }

    private static Bitmap? LoadLogoBitmap()
    {
        try
        {
            var stream = System.Windows.Application.GetResourceStream(
                new Uri("pack://application:,,,/Assets/logo.png"))?.Stream;
            if (stream is not null)
            {
                using (stream)
                {
                    return new Bitmap(stream);
                }
            }
        }
        catch
        {
            // fall through
        }

        var path = System.IO.Path.Combine(AppContext.BaseDirectory, "Assets", "logo.png");
        return System.IO.File.Exists(path) ? new Bitmap(path) : null;
    }

    private static Icon CreateIconFromBitmap(Bitmap bitmap)
    {
        var handle = bitmap.GetHicon();
        try
        {
            using var source = Icon.FromHandle(handle);
            return (Icon)source.Clone();
        }
        finally
        {
            DestroyIcon(handle);
        }
    }

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern bool DestroyIcon(IntPtr handle);

    public void SetStatus(string text)
    {
        _icon.Text = text.Length > 63 ? text[..63] : text;
        _icon.ShowBalloonTip(
            3000,
            "FrogsWork File Storage",
            text,
            Forms.ToolTipIcon.Info);
    }

    public void Dispose()
    {
        _icon.Visible = false;
        _icon.Dispose();
    }
}
