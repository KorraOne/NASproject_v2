import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getStorageOverview } from "../api/storage";
import { listSnapshots } from "../api/snapshots";
import { getSshStatus, getSystemInfo } from "../api/system";
import { ApiRequestError, formatBytes, formatPercent } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import type { StorageOverview } from "../types";
import type { SystemInfo } from "../api/system";
import type { Snapshot } from "../api/snapshots";

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatSnapshotAge(createdAt: string): string {
  const created = new Date(createdAt);
  const diffMs = Date.now() - created.getTime();
  const hours = Math.floor(diffMs / 3_600_000);
  if (hours < 1) return "less than an hour ago";
  if (hours < 48) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export function DashboardPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [storage, setStorage] = useState<StorageOverview | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [sshEnabled, setSshEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [info, storageData, snapshotList] = await Promise.all([
        getSystemInfo(),
        getStorageOverview(),
        listSnapshots(),
      ]);
      setSystemInfo(info);
      setStorage(storageData);
      setSnapshots(snapshotList);
      try {
        const ssh = await getSshStatus();
        setSshEnabled(ssh.remote_enabled);
      } catch {
        setSshEnabled(false);
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const alerts = useMemo(() => {
    const items: { kind: "warning" | "info"; message: string; link?: string }[] = [];
    if (storage) {
      const pct = (storage.used_bytes / storage.total_bytes) * 100;
      if (pct >= 80) {
        items.push({
          kind: "warning",
          message: `Storage is ${Math.round(pct)}% full. Consider freeing space or adjusting quotas.`,
          link: "/storage",
        });
      }
    }
    if (sshEnabled) {
      items.push({
        kind: "info",
        message: "Remote support SSH is enabled.",
        link: "/system",
      });
    }
    if (snapshots.length === 0) {
      items.push({
        kind: "warning",
        message: "No backups yet. Create one from Backups.",
        link: "/snapshots",
      });
    } else {
      const newest = snapshots[0];
      const ageMs = Date.now() - new Date(newest.created_at).getTime();
      if (ageMs > 48 * 3_600_000) {
        items.push({
          kind: "warning",
          message: `Latest backup is ${formatSnapshotAge(newest.created_at)}.`,
          link: "/snapshots",
        });
      }
    }
    return items;
  }, [storage, sshEnabled, snapshots]);

  if (loading) return <Loading label="Loading dashboard…" />;
  if (!systemInfo || !storage) return <ErrorBanner message={error ?? "No data."} />;

  const usedPct = formatPercent(storage.used_bytes, storage.total_bytes);
  const primaryIp = systemInfo.ips[0] ?? "frogswork.local";
  const latestSnapshot = snapshots[0] ?? null;

  return (
    <div className="page">
      <PageIntro
        title="Dashboard"
        lede="A quick look at your FrogsWork box."
        action={
          <button type="button" className="btn btn-ghost" onClick={load}>
            Refresh
          </button>
        }
      />
      <ErrorBanner message={error} />

      {alerts.length > 0 ? (
        <section className="dashboard-alerts section-card">
          {alerts.map((alert) => (
            <div key={alert.message} className={`alert-banner alert-${alert.kind}`} role="status">
              {alert.message}
              {alert.link ? (
                <>
                  {" "}
                  <Link to={alert.link}>View →</Link>
                </>
              ) : null}
            </div>
          ))}
        </section>
      ) : (
        <div className="alert-banner alert-ok" role="status">
          Everything looks good.
        </div>
      )}

      <div className="dashboard-grid section-card">
        <section className="card">
          <h2>System</h2>
          <dl className="stat-list">
            <div>
              <dt>Name on network</dt>
              <dd>{systemInfo.hostname}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>{primaryIp}</dd>
            </div>
            <div>
              <dt>Running since</dt>
              <dd>{formatUptime(systemInfo.uptime_seconds)}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{systemInfo.version}</dd>
            </div>
          </dl>
          <p className="card-footer-link">
            <Link to="/system">System settings →</Link>
          </p>
        </section>

        <section className="card storage-card">
          <h2>Storage</h2>
          <div className="storage-bar" aria-hidden>
            <div className="storage-bar-fill" style={{ width: `${usedPct}%` }} />
          </div>
          <p className="storage-summary">
            <strong>{formatBytes(storage.used_bytes)}</strong> used of{" "}
            <strong>{formatBytes(storage.total_bytes)}</strong> ({usedPct}%)
          </p>
          <dl className="stat-list compact-stats">
            <div>
              <dt>File users</dt>
              <dd>{storage.file_user_count}</dd>
            </div>
            <div>
              <dt>Shared folders</dt>
              <dd>{storage.shared_folder_count}</dd>
            </div>
          </dl>
          <p className="card-footer-link">
            <Link to="/storage">Storage details →</Link>
          </p>
        </section>

        <section className="card">
          <h2>Latest backup</h2>
          {latestSnapshot ? (
            <dl className="stat-list">
              <div>
                <dt>Date</dt>
                <dd>{latestSnapshot.snapshot_date}</dd>
              </div>
              <div>
                <dt>Type</dt>
                <dd>{latestSnapshot.kind}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{formatSnapshotAge(latestSnapshot.created_at)}</dd>
              </div>
            </dl>
          ) : (
            <p className="muted">No backups yet.</p>
          )}
          <p className="card-footer-link">
            <Link to="/snapshots">Manage backups →</Link>
          </p>
        </section>
      </div>

      <section className="card section-card">
        <h2>Quick actions</h2>
        <div className="quick-actions">
          <Link to="/users/new" className="btn btn-primary">
            Add user
          </Link>
          <Link to="/folders/new" className="btn btn-ghost">
            Add folder
          </Link>
          <Link to="/snapshots" className="btn btn-ghost">
            Manage backups
          </Link>
          <Link to="/permissions" className="btn btn-ghost">
            Permissions
          </Link>
          <Link to="/guide" className="btn btn-ghost">
            Setup guide
          </Link>
          <a className="btn btn-ghost" href="/api/helper/download">
            Download helper
          </a>
        </div>
      </section>
    </div>
  );
}
