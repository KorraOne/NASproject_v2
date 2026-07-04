import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  getSshStatus,
  getSystemInfo,
  rebootAppliance,
  setSshStatus,
  shutdownAppliance,
  type SystemInfo,
} from "../api/system";
import { ApiRequestError, formatBytes, formatPercent } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";

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

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>System</h1>
          <p className="lede">Appliance health, network details, and support access controls.</p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={load}>
          Refresh
        </button>
      </header>

      <ErrorBanner message={error} />

      <div className="storage-grid">
        <section className="card">
          <h2>Network</h2>
          <dl className="stat-list">
            <div>
              <dt>Hostname</dt>
              <dd>{info.hostname}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>{info.ips.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt>Dashboard URL</dt>
              <dd>
                <code>http://frogswork.local</code>
              </dd>
            </div>
            <div>
              <dt>Uptime</dt>
              <dd>{formatUptime(info.uptime_seconds)}</dd>
            </div>
            <div>
              <dt>Software version</dt>
              <dd>{info.version}</dd>
            </div>
          </dl>
        </section>

        <section className="card storage-card">
          <h2>Data volume</h2>
          <p className="storage-mount">
            <code>{info.data_mount}</code>
          </p>
          <div className="storage-bar" aria-hidden>
            <div className="storage-bar-fill" style={{ width: `${dataPct}%` }} />
          </div>
          <p className="storage-summary">
            <strong>{formatBytes(info.data_used_bytes)}</strong> used of{" "}
            <strong>{formatBytes(info.data_total_bytes)}</strong> ({dataPct}%)
          </p>
        </section>
      </div>

      <section className="card panel">
        <h2>Remote support SSH</h2>
        <p className="lede">
          When enabled, technicians can connect over SSH from your network. Disabled by default for
          security.
        </p>
        <label className="checkbox-row ssh-toggle">
          <input type="checkbox" checked={sshEnabled} disabled={busy} onChange={onToggleSsh} />
          Allow remote support SSH
        </label>
      </section>

      <section className="card panel">
        <h2>Power</h2>
        <p className="lede">Restart or shut down the appliance. File sharing will stop until it is back on.</p>
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={() => setPowerAction("reboot")}>
            Reboot
          </button>
          <button type="button" className="btn btn-danger" onClick={() => setPowerAction("shutdown")}>
            Shut down
          </button>
        </div>
      </section>

      <section className="card panel">
        <h2>Windows helper app</h2>
        <p className="lede">
          Employees use the helper app to map network drives. Download will be available here in a
          future update.
        </p>
      </section>

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
