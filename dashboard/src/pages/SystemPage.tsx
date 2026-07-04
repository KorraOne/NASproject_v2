import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getSshStatus,
  getSystemInfo,
  rebootAppliance,
  setSshStatus,
  shutdownAppliance,
  type SystemInfo,
} from "../api/system";
import { ApiRequestError, formatBytes, formatPercent } from "../api/client";
import { CopyButton } from "../components/CopyButton";
import { ErrorBanner } from "../components/ErrorBanner";
import { GuideCard } from "../components/GuideCard";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { StepGuide } from "../components/StepGuide";

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function SystemPage() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [sshEnabled, setSshEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [powerAction, setPowerAction] = useState<"reboot" | "shutdown" | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const systemInfo = await getSystemInfo();
      setInfo(systemInfo);
      try {
        const ssh = await getSshStatus();
        setSshEnabled(ssh.remote_enabled);
      } catch {
        // SSH status is optional if integration is unavailable
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load system info.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onToggleSsh() {
    setBusy(true);
    setError(null);
    try {
      const next = !sshEnabled;
      const result = await setSshStatus(next);
      setSshEnabled(result.remote_enabled);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not update SSH setting.");
    } finally {
      setBusy(false);
    }
  }

  async function onPowerConfirm(e: FormEvent) {
    e.preventDefault();
    if (!powerAction) return;
    setBusy(true);
    setError(null);
    try {
      const result =
        powerAction === "reboot"
          ? await rebootAppliance(true)
          : await shutdownAppliance(true);
      setPowerAction(null);
      alert(result.message);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Power action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading system info…" />;
  if (!info) return <ErrorBanner message={error ?? "No data."} />;

  const dataPct = formatPercent(info.data_used_bytes, info.data_total_bytes);
  const primaryIp = info.ips[0] ?? "";
  const dashboardUrl = primaryIp ? `http://${primaryIp}` : "http://frogswork.local";

  const helperSteps = [
    {
      title: "Create their account",
      body: (
        <p>
          Go to <Link to="/users">Users</Link>, click <strong>Add user</strong>, and note the username and
          password you give them.
        </p>
      ),
    },
    {
      title: "Download the helper app",
      body: <p>Send them the installer below, or download it on their Windows PC.</p>,
      action: (
        <a className="btn btn-primary btn-large" href="/api/helper/download">
          Download FrogsWork Helper
        </a>
      ),
    },
    {
      title: "Install and open",
      body: (
        <>
          <p>Run <strong>FrogsWork.Helper.exe</strong>. Windows may ask whether to allow the app — choose Run or Allow.</p>
          <GuideCard variant="tip" title="Windows SmartScreen">
            You may see a blue warning that the app is unrecognized. Click <strong>More info</strong>, then{" "}
            <strong>Run anyway</strong>. We will offer a signed installer in a future update.
          </GuideCard>
        </>
      ),
    },
    {
      title: "Sign in",
      body: (
        <p>
          In the helper, use the address <strong>{primaryIp || "shown above"}</strong>, their username, and the
          password you created. Stick to the IP address if the name does not work.
        </p>
      ),
    },
    {
      title: "Done",
      body: (
        <p>
          Their personal files appear on drive <strong>U:</strong> and shared folders on <strong>S:</strong> (and
          other letters) in File Explorer.
        </p>
      ),
    },
  ];

  return (
    <div className="page">
      <PageIntro
        title="System"
        lede="Set up Windows PCs for your team, and manage appliance settings."
        action={
          <button type="button" className="btn btn-ghost" onClick={load}>
            Refresh
          </button>
        }
      />

      <ErrorBanner message={error} />

      <section className="card featured-card section-card">
        <h2>Set up a Windows PC</h2>
        <p className="section-card-lede">
          Follow these steps once per employee. You only need to do the user account part — they handle the rest
          on their computer.
        </p>
        <StepGuide steps={helperSteps} />
      </section>

      <div className="storage-grid section-card">
        <section className="card">
          <h2>Your FrogsWork box</h2>
          <dl className="stat-list">
            <div>
              <dt>Name on network</dt>
              <dd>{info.hostname}</dd>
            </div>
            <div>
              <dt>Address for helper sign-in</dt>
              <dd>
                {primaryIp || "—"}
                {primaryIp ? <CopyButton text={primaryIp} label="Copy IP" /> : null}
              </dd>
            </div>
            <div>
              <dt>Open dashboard in browser</dt>
              <dd>
                {dashboardUrl}
                <CopyButton text={dashboardUrl} label="Copy link" />
              </dd>
            </div>
            <div>
              <dt>Running since</dt>
              <dd>{formatUptime(info.uptime_seconds)}</dd>
            </div>
          </dl>
        </section>

        <section className="card storage-card">
          <h2>Storage space</h2>
          <div className="storage-bar" aria-hidden>
            <div className="storage-bar-fill" style={{ width: `${dataPct}%` }} />
          </div>
          <p className="storage-summary">
            <strong>{formatBytes(info.data_used_bytes)}</strong> used of{" "}
            <strong>{formatBytes(info.data_total_bytes)}</strong> ({dataPct}%)
          </p>
        </section>
      </div>

      <section className="card panel section-card">
        <h2>Remote support</h2>
        <p className="section-card-lede">
          Allow a technician to connect over SSH from your network. Leave this off unless you need help.
        </p>
        <label className="checkbox-row ssh-toggle">
          <input type="checkbox" checked={sshEnabled} disabled={busy} onChange={onToggleSsh} />
          Allow remote support SSH
        </label>
      </section>

      <section className="card panel section-card">
        <h2>Restart or shut down</h2>
        <p className="section-card-lede">
          File sharing stops while the box is off or restarting. Usually takes about a minute to come back.
        </p>
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={() => setPowerAction("reboot")}>
            Reboot
          </button>
          <button type="button" className="btn btn-danger" onClick={() => setPowerAction("shutdown")}>
            Shut down
          </button>
        </div>
      </section>

      <details className="card details-toggle section-card">
        <summary>Advanced details</summary>
        <div className="details-panel">
          <dl className="stat-list">
            <div>
              <dt>Software version</dt>
              <dd>{info.version}</dd>
            </div>
            <div>
              <dt>Data folder</dt>
              <dd>
                <code>{info.data_mount}</code>
              </dd>
            </div>
            <div>
              <dt>All network addresses</dt>
              <dd>{info.ips.join(", ") || "—"}</dd>
            </div>
          </dl>
        </div>
      </details>

      {powerAction && (
        <section className="card restore-dialog">
          <h2>{powerAction === "reboot" ? "Reboot FrogsWork?" : "Shut down FrogsWork?"}</h2>
          <p>
            {powerAction === "reboot"
              ? "The dashboard and file sharing will be unavailable for about a minute."
              : "The appliance will power off. Use the physical power button to turn it back on."}
          </p>
          <form onSubmit={onPowerConfirm} className="form-actions">
            <button type="submit" className="btn btn-danger" disabled={busy}>
              {busy ? "Working…" : powerAction === "reboot" ? "Reboot now" : "Shut down now"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setPowerAction(null)}>
              Cancel
            </button>
          </form>
        </section>
      )}
    </div>
  );
}
