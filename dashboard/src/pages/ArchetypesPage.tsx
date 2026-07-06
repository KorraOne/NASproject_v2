import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteArchetype, listArchetypes } from "../api/archetypes";
import { ApiRequestError } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { useToast } from "../components/Toast";
import { UsersSubNav } from "../components/UsersSubNav";
import type { Archetype } from "../types";

export function ArchetypesPage() {
  const { showToast } = useToast();
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Archetype | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setArchetypes(await listArchetypes());
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load archetypes.");
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
      await deleteArchetype(deleteTarget.id);
      const name = deleteTarget.name;
      setDeleteTarget(null);
      showToast(`Deleted archetype "${name}".`);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Delete failed.");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) return <Loading label="Loading archetypes…" />;

  return (
    <div className="page">
      <UsersSubNav />
      <PageIntro
        title="Archetypes"
        lede="Reusable permission templates. Assign an archetype when adding or editing a person."
        action={
          <Link to="/users/archetypes/new" className="btn btn-primary">
            Create archetype
          </Link>
        }
      />
      <ErrorBanner message={error} />
      <section className="card">
        {archetypes.length === 0 ? (
          <EmptyState
            title="No archetypes yet"
            description="Create a template for common roles like Accountant or Field Tech."
            action={
              <Link to="/users/archetypes/new" className="btn btn-primary">
                Create archetype
              </Link>
            }
          />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>People</th>
                <th>Personal folders</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {archetypes.map((archetype) => (
                <tr key={archetype.id}>
                  <td>
                    {archetype.name}
                    {archetype.is_system ? <span className="effective-badge"> System</span> : null}
                  </td>
                  <td>{archetype.user_count}</td>
                  <td>{archetype.can_view_all_personal ? "All (Super User)" : "Own only"}</td>
                  <td className="actions">
                    <Link to={`/users/archetypes/${archetype.id}/edit`} className="btn btn-small">
                      Edit
                    </Link>
                    {!archetype.is_system ? (
                      <button
                        type="button"
                        className="btn btn-small btn-danger"
                        onClick={() => setDeleteTarget(archetype)}
                      >
                        Delete
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete archetype?"
        message={
          deleteTarget
            ? `Delete "${deleteTarget.name}"? Reassign any people using this archetype first.`
            : ""
        }
        confirmLabel="Delete archetype"
        danger
        busy={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
