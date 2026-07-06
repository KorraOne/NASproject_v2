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
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { Modal } from "../components/Modal";
import { PageIntro } from "../components/PageIntro";
import { useToast } from "../components/Toast";
import type { SnapshotBrowseEntry, SnapshotSettings } from "../types";

function kindLabel(kind: string): string {
  if (kind === "daily") return "Daily";
  if (kind === "weekly") return "Weekly";
  if (kind === "monthly") return "Monthly";
  return kind;
}

export function SnapshotsPage() {
  const { showToast } = useToast();
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [settings, setSettings] = useState<SnapshotSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [scheduleOpen, setScheduleOpen] = useState(false);
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
      setError(err instanceof ApiRequestError ? err.message : "Could not load backups.");
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
    setBrowseLoading(true);
    setError(null);
    try {
      setEntries(await browseSnapshot(snapshot.id, path));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not browse backup.");
      setEntries([]);
    } finally {
      setBrowseLoading(false);
    }
  }

  function closeBrowse() {
    setSelected(null);
    setBrowsePath("");
    setEntries([]);
    setRestoreTarget(null);
    setConfirmToken("");
  }

  async function onCreate() {
    setCreating(true);
    setError(null);
    try {
      await createSnapshot();
      await load();
      showToast("Backup created.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not create backup.");
    } finally {
      setCreating(false);
    }
  }

  async function onSaveSettings(e: FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setSavingSettings(true);
    setError(null);
    try {
      const updated = await updateSnapshotSettings(settings);
      setSettings(updated);
      showToast("Backup schedule saved.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not save settings.");
    } finally {
      setSavingSettings(false);
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
    setRestoring(true);
    setError(null);
    try {
      await restoreSnapshot(selected.id, restoreTarget.path, confirmToken);
      setRestoreTarget(null);
      setConfirmToken("");
      showToast("File restored.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Restore failed.");
    } finally {
      setRestoring(false);
    }
  }

  const parentPath = browsePath.includes("/")
    ? browsePath.split("/").slice(0, -1).join("/")
    : "";

  if (loading) return <Loading label="Loading backups…" />;

  return (
    <div className="page">
      <PageIntro
        title="Backups"
        lede="Restore older versions of files. A backup runs automatically every night."
        action={
          <div className="inline-actions">
            <button type="button" className="btn btn-ghost" onClick={load}>
              Refresh
            </button>
            <button type="button" className="btn btn-primary" disabled={creating} onClick={onCreate}>
              {creating ? "Creating…" : "Create backup now"}
            </button>
          </div>
        }
      />

      <ErrorBanner message={error} />

      <div className="backups-layout">
        <div className="backups-sidebar">
          <section className="card">
            <h2>Backup history</h2>
            {snapshots.length === 0 ? (
              <EmptyState
                title="No backups yet"
                description="Create one now or wait for tonight's automatic backup."
                action={
                  <button type="button" className="btn btn-primary" disabled={creating} onClick={onCreate}>
                    Create backup now
                  </button>
                }
              />
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
                        <button
                          type="button"
                          className="btn btn-small"
                          onClick={() => loadBrowse(snap, "")}
                        >
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
            <button
              type="button"
              className="collapsible-trigger"
              aria-expanded={scheduleOpen}
              onClick={() => setScheduleOpen((open) => !open)}
            >
              Automatic backups
              <span className="collapsible-chevron">{scheduleOpen ? "−" : "+"}</span>
            </button>
            {scheduleOpen && settings ? (
              <form onSubmit={onSaveSettings} className="stack-form collapsible-body">
                <label>
                  Nightly backup hour (0–23)
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
                  Keep daily backups
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
                  Keep weekly backups
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
                  Keep monthly backups
                  <input
                    type="number"
                    min={1}
                    value={settings.retention_monthly}
                    onChange={(e) =>
                      setSettings({ ...settings, retention_monthly: Number(e.target.value) })
                    }
                  />
                </label>
                <button type="submit" className="btn btn-primary" disabled={savingSettings}>
                  {savingSettings ? "Saving…" : "Save schedule"}
                </button>
              </form>
            ) : null}
          </section>
        </div>

        <section className="card backups-detail">
          {!selected ? (
            <EmptyState
              title="Browse a backup"
              description="Select a backup from the list to view and restore files."
            />
          ) : (
            <>
              <div className="backups-detail-header">
                <h2>Browse {selected.snapshot_date}</h2>
                <button type="button" className="btn btn-ghost btn-small" onClick={closeBrowse}>
                  Close
                </button>
              </div>
              <p className="breadcrumb">
                <button type="button" className="link-btn" onClick={() => loadBrowse(selected, "")}>
                  /
                </button>
                {browsePath
                  ? browsePath.split("/").map((part, index, parts) => {
                      const path = parts.slice(0, index + 1).join("/");
                      return (
                        <span key={path}>
                          {" / "}
                          <button
                            type="button"
                            className="link-btn"
                            onClick={() => loadBrowse(selected, path)}
                          >
                            {part}
                          </button>
                        </span>
                      );
                    })
                  : null}
              </p>
              {browseLoading ? (
                <Loading label="Loading folder…" />
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th aria-label="Actions" />
                    </tr>
                  </thead>
                  <tbody>
                    {browsePath ? (
                      <tr>
                        <td>
                          <span className="browse-dir-label">..</span>
                        </td>
                        <td className="actions">
                          <button
                            type="button"
                            className="btn btn-small"
                            onClick={() => loadBrowse(selected, parentPath)}
                          >
                            Up
                          </button>
                        </td>
                      </tr>
                    ) : null}
                    {entries.length === 0 ? (
                      <tr>
                        <td colSpan={2} className="muted">
                          This folder is empty.
                        </td>
                      </tr>
                    ) : (
                      entries.map((entry) => (
                        <tr key={entry.path}>
                          <td>
                            {entry.is_dir ? (
                              <span className="browse-dir-label">{entry.name}</span>
                            ) : (
                              entry.name
                            )}
                          </td>
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
                              <button
                                type="button"
                                className="btn btn-small"
                                onClick={() => startRestore(entry)}
                              >
                                Restore
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </>
          )}
        </section>
      </div>

      <Modal
        open={restoreTarget !== null}
        title="Restore this file?"
        onClose={() => {
          if (!restoring) {
            setRestoreTarget(null);
            setConfirmToken("");
          }
        }}
        footer={
          <div className="form-actions">
            <button
              type="button"
              className="btn btn-danger"
              disabled={restoring}
              onClick={confirmRestore}
            >
              {restoring ? "Restoring…" : "Restore file"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={restoring}
              onClick={() => {
                setRestoreTarget(null);
                setConfirmToken("");
              }}
            >
              Cancel
            </button>
          </div>
        }
      >
        <p>
          Restore <code>{restoreTarget?.path}</code> from the <strong>{selected?.snapshot_date}</strong>{" "}
          backup? This overwrites the current file if it exists.
        </p>
      </Modal>
    </div>
  );
}
