import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  browseSnapshot,
  createSnapshot,
  getRestoreToken,
  getSnapshotSettings,
  listSnapshots,
  restoreSnapshot,
  updateSnapshotSettings,
  type Snapshot,
} from "../api/snapshots";
import { ApiRequestError } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import type { SnapshotBrowseEntry, SnapshotSettings } from "../types";

function kindLabel(kind: string): string {
  if (kind === "daily") return "Daily";
  if (kind === "weekly") return "Weekly";
  if (kind === "monthly") return "Monthly";
  return kind;
}

export function SnapshotsPage() {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [settings, setSettings] = useState<SnapshotSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Snapshot | null>(null);
  const [browsePath, setBrowsePath] = useState("");
  const [entries, setEntries] = useState<SnapshotBrowseEntry[]>([]);
  const [restoreTarget, setRestoreTarget] = useState<SnapshotBrowseEntry | null>(null);
  const [confirmToken, setConfirmToken] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [snapList, snapSettings] = await Promise.all([listSnapshots(), getSnapshotSettings()]);
      setSnapshots(snapList);
      setSettings(snapSettings);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load snapshots.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function loadBrowse(snapshot: Snapshot, path: string) {
    setSelected(snapshot);
    setBrowsePath(path);
    setRestoreTarget(null);
    setConfirmToken("");
    try {
      setEntries(await browseSnapshot(snapshot.id, path));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not browse snapshot.");
      setEntries([]);
    }
  }

  async function onCreate() {
    setBusy(true);
    setError(null);
    try {
      await createSnapshot();
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not create snapshot.");
    } finally {
      setBusy(false);
    }
  }

  async function onSaveSettings(e: FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateSnapshotSettings(settings);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not save settings.");
    } finally {
      setBusy(false);
    }
  }

  async function startRestore(entry: SnapshotBrowseEntry) {
    if (!selected || entry.is_dir) return;
    setError(null);
    try {
      const token = await getRestoreToken(selected.id, entry.path);
      setRestoreTarget(entry);
      setConfirmToken(token.confirm_token);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not prepare restore.");
    }
  }

  async function confirmRestore() {
    if (!selected || !restoreTarget || !confirmToken) return;
    setBusy(true);
    setError(null);
    try {
      await restoreSnapshot(selected.id, restoreTarget.path, confirmToken);
      setRestoreTarget(null);
      setConfirmToken("");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Restore failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading snapshots…" />;

  return (
    <div className="page">
      <PageIntro
        title="Backups"
        lede="Restore older versions of files. A backup runs automatically every night."
        action={
          <button type="button" className="btn btn-primary" disabled={busy} onClick={onCreate}>
            {busy ? "Working…" : "Create backup now"}
          </button>
        }
      />

      <ErrorBanner message={error} />

      <div className="page-grid">
        <section className="card">
          {snapshots.length === 0 ? (
            <p className="muted">No snapshots yet. Create one now or wait for tonight&apos;s automatic backup.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {snapshots.map((snap) => (
                  <tr key={snap.id} className={selected?.id === snap.id ? "selected" : undefined}>
                    <td>{snap.snapshot_date}</td>
                    <td>{kindLabel(snap.kind)}</td>
                    <td className="actions">
                      <button type="button" className="btn btn-small" onClick={() => loadBrowse(snap, "")}>
                        Browse
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card panel">
          <h2>Schedule & retention</h2>
          {settings && (
            <form onSubmit={onSaveSettings} className="stack-form">
              <label>
                Nightly snapshot hour (0–23)
                <input
                  type="number"
                  min={0}
                  max={23}
                  value={settings.snapshot_hour}
                  onChange={(e) =>
                    setSettings({ ...settings, snapshot_hour: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Keep daily snapshots
                <input
                  type="number"
                  min={1}
                  value={settings.retention_daily}
                  onChange={(e) =>
                    setSettings({ ...settings, retention_daily: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Keep weekly snapshots
                <input
                  type="number"
                  min={1}
                  value={settings.retention_weekly}
                  onChange={(e) =>
                    setSettings({ ...settings, retention_weekly: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Keep monthly snapshots
                <input
                  type="number"
                  min={1}
                  value={settings.retention_monthly}
                  onChange={(e) =>
                    setSettings({ ...settings, retention_monthly: Number(e.target.value) })
                  }
                />
              </label>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Save settings
              </button>
            </form>
          )}
        </section>
      </div>

      {selected && (
        <section className="card browse-panel">
          <h2>Browse {selected.snapshot_date}</h2>
          <p className="breadcrumb">
            <button type="button" className="link-btn" onClick={() => loadBrowse(selected, "")}>
              /
            </button>
            {browsePath &&
              browsePath.split("/").map((part, index, parts) => {
                const path = parts.slice(0, index + 1).join("/");
                return (
                  <span key={path}>
                    {" / "}
                    <button type="button" className="link-btn" onClick={() => loadBrowse(selected, path)}>
                      {part}
                    </button>
                  </span>
                );
              })}
          </p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.path}>
                  <td>{entry.is_dir ? `📁 ${entry.name}` : entry.name}</td>
                  <td className="actions">
                    {entry.is_dir ? (
                      <button
                        type="button"
                        className="btn btn-small"
                        onClick={() => loadBrowse(selected, entry.path)}
                      >
                        Open
                      </button>
                    ) : (
                      <button type="button" className="btn btn-small" onClick={() => startRestore(entry)}>
                        Restore
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {restoreTarget && (
        <section className="card restore-dialog">
          <h2>Confirm restore</h2>
          <p>
            Restore <code>{restoreTarget.path}</code> from snapshot{" "}
            <strong>{selected?.snapshot_date}</strong>? This overwrites the current file if it exists.
          </p>
          <p className="hint">
            Confirmation code: <code>{confirmToken}</code>
          </p>
          <div className="form-actions">
            <button type="button" className="btn btn-primary" disabled={busy} onClick={confirmRestore}>
              {busy ? "Restoring…" : "Restore file"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setRestoreTarget(null);
                setConfirmToken("");
              }}
            >
              Cancel
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
