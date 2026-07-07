import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  applyLatestUpdate,
  checkForUpdates,
  getSshStatus,
  getStorageSettings,
  getSystemInfo,
  rebootAppliance,
  setSshStatus,
  shutdownAppliance,
  updateStorageSettings,
  type SystemInfo,
  type UpdateCheck,
} from "../api/system";
import { ApiRequestError, formatBytes, formatPercent } from "../api/client";
import { CopyButton } from "../components/CopyButton";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { Modal } from "../components/Modal";
import { PageIntro } from "../components/PageIntro";

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
  const [defaultQuotaGb, setDefaultQuotaGb] = useState("");
  const [applyDefaultQuota, setApplyDefaultQuota] = useState(false);
  const [updateStatus, setUpdateStatus] = useState<UpdateCheck | null>(null);
  const [updateAction, setUpdateAction] = useState<"apply" | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [infoBanner, setInfoBanner] = useState<string | null>(null);
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
        // optional
      }
      try {
        const storage = await getStorageSettings();
        setDefaultQuotaGb(
          storage.default_personal_quota_bytes
            ? String(storage.default_personal_quota_bytes / 1024 ** 3)
            : "",
        );
      } catch {
        // optional
      }
      try {
        const updates = await checkForUpdates();
        setUpdateStatus(updates);
      } catch {
        // optional
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

  async function onSaveDefaultQuota(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const quotaBytes =
        defaultQuotaGb.trim() === "" ? null : Math.round(parseFloat(defaultQuotaGb) * 1024 ** 3);
      if (quotaBytes !== null && (Number.isNaN(quotaBytes) || quotaBytes <= 0)) {
        setError("Default cap must be a positive number of gigabytes, or leave blank.");
        setBusy(false);
        return;
      }
      const result = await updateStorageSettings({
        default_personal_quota_bytes: quotaBytes,
        apply_to_uncapped_users: applyDefaultQuota,
      });
      setDefaultQuotaGb(
        result.default_personal_quota_bytes
          ? String(result.default_personal_quota_bytes / 1024 ** 3)
          : "",
      );
      setApplyDefaultQuota(false);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not save default cap.");
    } finally {
      setBusy(false);
    }
  }

  async function onToggleSsh() {
    setBusy(true);
    setError(null);
    try {
      const result = await setSshStatus(!sshEnabled);
      setSshEnabled(result.remote_enabled);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not update SSH setting.");
    } finally {
      setBusy(false);
    }
  }

  async function onPowerConfirm() {
    if (!powerAction) return;
    setBusy(true);
    setError(null);
    setPowerAction(null);
    const isReboot = powerAction === "reboot";
    setInfoBanner(
      isReboot
        ? "Rebooting… the dashboard may go offline for 1–3 minutes. Refresh this page when the box is back."
        : "Shutting down… the dashboard will go offline. Use the power button to turn the box back on.",
    );
    try {
      if (isReboot) {
        await rebootAppliance(true);
      } else {
        await shutdownAppliance(true);
      }
    } catch (err) {
      if (isReboot) {
        setInfoBanner(
          "Reboot started. If this page stopped responding, wait 1–3 minutes and refresh.",
        );
      } else {
        setError(err instanceof ApiRequestError ? err.message : "Power action failed.");
        setInfoBanner(null);
      }
    } finally {
      setBusy(false);
    }
  }

  async function onCheckUpdates() {
    setBusy(true);
    setError(null);
    try {
      const updates = await checkForUpdates();
      setUpdateStatus(updates);
      if (!updates.updates_enabled) {
        setInfoBanner(
          "Updates aren’t configured yet on this appliance. Set FROGSWORK_UPDATE_MANIFEST_URL on the box to enable.",
        );
      } else if (updates.update_available) {
        setInfoBanner(`Update available: ${updates.available_version}.`);
      } else {
        setInfoBanner("You’re up to date.");
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not check for updates.");
    } finally {
      setBusy(false);
    }
  }

  async function onApplyUpdateConfirm() {
    setBusy(true);
    setError(null);
    setUpdateAction(null);
    setInfoBanner(
      "Applying update… the dashboard may go offline briefly. Refresh this page in 1–3 minutes.",
    );
    try {
      const result = await applyLatestUpdate();
      setInfoBanner(result.message);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Update failed.");
      setInfoBanner(null);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading system info…" />;
  if (!info) return <ErrorBanner message={error ?? "No data."} />;

  const dataPct = formatPercent(info.data_used_bytes, info.data_total_bytes);
  const primaryIp = info.ips[0] ?? "";
  const dashboardUrl = primaryIp ? `http://${primaryIp}` : "http://frogswork.local";

  return (
    <div className="page">
      <PageIntro
        title="System"
        lede="Appliance settings and storage. For employee setup, see the Setup guide."
        action={
          <button type="button" className="btn btn-ghost" onClick={load} disabled={busy}>
            Refresh
          </button>
        }
      />

      {infoBanner ? (
        <div className="info-banner" role="status">
          {infoBanner}
        </div>
      ) : null}
      <ErrorBanner message={error} />

      <p className="page-footer-hint">
        <Link to="/guide">Open setup guide →</Link> ·{" "}
        <a href="/help" target="_blank" rel="noreferrer">
          Employee help page
        </a>
      </p>

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
        <h2>Personal folder defaults</h2>
        <p className="section-card-lede">
          Default maximum size for new personal folders. Applies when you add file users.
        </p>
        <form onSubmit={onSaveDefaultQuota} className="stack-form">
          <label>
            Default personal folder cap (GB)
            <input
              type="number"
              min="0"
              step="0.1"
              value={defaultQuotaGb}
              onChange={(e) => setDefaultQuotaGb(e.target.value)}
            />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={applyDefaultQuota}
              onChange={(e) => setApplyDefaultQuota(e.target.checked)}
            />
            Apply to existing users who have no individual cap
          </label>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Saving…" : "Save default cap"}
            </button>
          </div>
        </form>
      </section>

      <section className="card panel section-card">
        <h2>Remote support</h2>
        <p className="section-card-lede">
          Controls SSH login to the Linux system on this box — not your dashboard password. When off,
          SSH is blocked. When on, anyone who can reach port 22 may try to log in with a Linux user
          account (for example the factory admin user). On your office LAN that is usually enough for
          support. Over the internet you would also need port forwarding on the customer router or a
          VPN; FrogsWork does not open that for you.
        </p>
        <label className="checkbox-row ssh-toggle">
          <input type="checkbox" checked={sshEnabled} disabled={busy} onChange={onToggleSsh} />
          Allow remote support SSH
        </label>
      </section>

      <section className="card panel section-card">
        <h2>Updates</h2>
        <p className="section-card-lede">
          Keep this appliance up to date without SSH. Updates are pulled from your release bucket.
        </p>
        <dl className="stat-list">
          <div>
            <dt>Current version</dt>
            <dd>{info.version}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              {updateStatus
                ? updateStatus.updates_enabled
                  ? updateStatus.update_available
                    ? `Update available: ${updateStatus.available_version ?? "—"}`
                    : "Up to date"
                  : "Not configured"
                : "—"}
            </dd>
          </div>
        </dl>
        {updateStatus?.notes ? (
          <p className="page-footer-hint" style={{ marginTop: "0.75rem" }}>
            {updateStatus.notes}
          </p>
        ) : null}
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={onCheckUpdates}>
            {busy ? "Checking…" : "Check for updates"}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy || !updateStatus?.updates_enabled || !updateStatus?.update_available}
            onClick={() => setUpdateAction("apply")}
          >
            Apply update
          </button>
        </div>
      </section>

      <section className="card panel section-card">
        <h2>Restart or shut down</h2>
        <p className="section-card-lede">
          File sharing stops while the box is off or restarting. Coming back usually takes 1–3 minutes.
        </p>
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => setPowerAction("reboot")}
          >
            Reboot
          </button>
          <button
            type="button"
            className="btn btn-danger"
            disabled={busy}
            onClick={() => setPowerAction("shutdown")}
          >
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

      <Modal
        open={powerAction !== null}
        title={powerAction === "reboot" ? "Reboot FrogsWork?" : "Shut down FrogsWork?"}
        onClose={() => setPowerAction(null)}
        footer={
          <div className="form-actions">
            <button
              type="button"
              className="btn btn-danger"
              disabled={busy}
              onClick={onPowerConfirm}
            >
              {powerAction === "reboot" ? "Reboot now" : "Shut down now"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setPowerAction(null)}>
              Cancel
            </button>
          </div>
        }
      >
        <p>
          {powerAction === "reboot"
            ? "The dashboard and file sharing will go offline. Allow 1–3 minutes before refreshing this page."
            : "The appliance will power off. Use the physical power button to turn it back on."}
        </p>
      </Modal>

      <Modal
        open={updateAction !== null}
        title="Apply update now?"
        onClose={() => setUpdateAction(null)}
        footer={
          <div className="form-actions">
            <button
              type="button"
              className="btn btn-danger"
              disabled={busy}
              onClick={onApplyUpdateConfirm}
            >
              {busy ? "Applying…" : "Apply update"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setUpdateAction(null)}>
              Cancel
            </button>
          </div>
        }
      >
        <p>
          This will download the latest release and restart services. The dashboard may go offline for
          1–3 minutes.
        </p>
      </Modal>
    </div>
  );
}
