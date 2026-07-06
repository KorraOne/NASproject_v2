import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteUser, listUsers } from "../api/users";
import { ApiRequestError } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { GettingStartedBanner } from "../components/GettingStartedBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { useToast } from "../components/Toast";
import { UsersSubNav } from "../components/UsersSubNav";
import type { FileUser } from "../types";

export function UsersPage() {
  const { showToast } = useToast();
  const [users, setUsers] = useState<FileUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<FileUser | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setUsers(await listUsers());
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load users.");
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
      await deleteUser(deleteTarget.id);
      setDeleteTarget(null);
      showToast(`Deleted ${deleteTarget.username}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Delete failed.");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) return <Loading label="Loading users…" />;

  return (
    <div className="page">
      <UsersSubNav />
      <PageIntro
        title="People"
        lede="File users sign in on their Windows PC and get a private folder plus shared access."
        action={
          <Link to="/users/new" className="btn btn-primary">
            Add user
          </Link>
        }
      />
      {users.length === 0 ? <GettingStartedBanner /> : null}
      <ErrorBanner message={error} />
      <section className="card">
        {users.length === 0 ? (
          <EmptyState
            title="No file users yet"
            description="Add someone who needs their own private folder and shared access."
            action={
              <Link to="/users/new" className="btn btn-primary">
                Add user
              </Link>
            }
          />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Display name</th>
                <th>Archetype</th>
                <th>Access</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <code>{user.username}</code>
                  </td>
                  <td>{user.display_name}</td>
                  <td>{user.archetype_name ?? "—"}</td>
                  <td>
                    {user.is_elevated ? (
                      <span className="effective-badge">Temporary access</span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td className="actions">
                    <Link to={`/users/${user.id}/edit`} className="btn btn-small">
                      Edit
                    </Link>
                    {user.archetype_name !== "Super User" ? (
                      <Link to={`/users/${user.id}/temporary-access`} className="btn btn-small">
                        Temporary access
                      </Link>
                    ) : null}
                    <button
                      type="button"
                      className="btn btn-small btn-danger"
                      onClick={() => setDeleteTarget(user)}
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

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete file user?"
        message={
          deleteTarget
            ? `Delete "${deleteTarget.username}"? This removes their private folder and cannot be undone.`
            : ""
        }
        confirmLabel="Delete user"
        danger
        busy={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
