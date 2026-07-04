import { useCallback, useEffect, useState } from "react";
import { getStorageOverview } from "../api/storage";
import { ApiRequestError, formatBytes, formatPercent } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import type { StorageOverview } from "../types";

export function StoragePage() {
  const [data, setData] = useState<StorageOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getStorageOverview());
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load storage info.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <Loading label="Loading storage…" />;
  if (!data) return <ErrorBanner message={error ?? "No data."} />;

  const usedPct = formatPercent(data.used_bytes, data.total_bytes);

  return (
    <div className="page">
      <PageIntro
        title="Storage"
        lede="How much space your files and backups are using."
        action={
          <button type="button" className="btn btn-ghost" onClick={load}>
            Refresh
          </button>
        }
      />

      <ErrorBanner message={error} />

      <div className="storage-grid">
        <section className="card storage-card">
          <h2>Data volume</h2>
          <p className="storage-mount">
            <code>{data.mount}</code>
          </p>
          <div className="storage-bar" aria-hidden>
            <div className="storage-bar-fill" style={{ width: `${usedPct}%` }} />
          </div>
          <p className="storage-summary">
            <strong>{formatBytes(data.used_bytes)}</strong> used of{" "}
            <strong>{formatBytes(data.total_bytes)}</strong> ({usedPct}%)
          </p>
          <p className="muted">{formatBytes(data.free_bytes)} free</p>
        </section>

        <section className="card">
          <h2>At a glance</h2>
          <dl className="stat-list">
            <div>
              <dt>File users</dt>
              <dd>{data.file_user_count}</dd>
            </div>
            <div>
              <dt>Shared folders</dt>
              <dd>{data.shared_folder_count}</dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
