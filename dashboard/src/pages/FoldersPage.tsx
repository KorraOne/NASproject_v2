import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteFolder, listFolders } from "../api/folders";
import { ApiRequestError } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { useToast } from "../components/Toast";
import type { SharedFolder } from "../types";

function gbFromBytes(bytes: number | null): string {
  if (bytes == null) return "—";
  return `${Math.round((bytes / 1024 ** 3) * 10) / 10} GB`;
}

export function FoldersPage() {
  const { showToast } = useToast();
  const [folders, setFolders] = useState<SharedFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SharedFolder | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFolders(await listFolders());
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load folders.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteFolder(deleteTarget.id);
      const name = deleteTarget.name;
      setDeleteTarget(null);
      showToast(`Deleted folder "${name}".`);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Delete failed.");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) return <Loading label="Loading folders…" />;

  return (
    <div className="page">
      <PageIntro
        title="Shared folders"
        lede="Team folders on drive W:. Set who can access each folder on Permissions."
        action={
          <Link to="/folders/new" className="btn btn-primary">
            Add folder
          </Link>
        }
      />
      <ErrorBanner message={error} />
      <section className="card">
        {folders.length === 0 ? (
          <EmptyState
            title="No shared folders yet"
            description="Create team folders like Projects or Invoices."
            action={
              <Link to="/folders/new" className="btn btn-primary">
                Add folder
              </Link>
            }
          />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>People with access</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {folders.map((folder) => (
                <tr key={folder.id}>
                  <td>
                    <div className="folder-name-cell">
                      <span className="folder-name">{folder.name}</span>
                      {folder.quota_bytes ? (
                        <span className="folder-meta">
                          Max size {gbFromBytes(folder.quota_bytes)}
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td>{folder.permissions.length}</td>
                  <td className="actions">
                    <Link to={`/folders/${folder.id}/edit`} className="btn btn-small">
                      Edit
                    </Link>
                    <button
                      type="button"
                      className="btn btn-small btn-danger"
                      onClick={() => setDeleteTarget(folder)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      <p className="page-footer-hint">
        <Link to="/permissions">Manage permissions →</Link>
      </p>

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete shared folder?"
        message={
          deleteTarget
            ? `Delete "${deleteTarget.name}"? The folder must be completely empty first.`
            : ""
        }
        confirmLabel="Delete folder"
        danger
        busy={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
