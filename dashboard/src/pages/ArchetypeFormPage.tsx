import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createArchetype,
  getArchetype,
  replaceArchetypePermissions,
  updateArchetype,
} from "../api/archetypes";
import { listFolders } from "../api/folders";
import { ApiRequestError } from "../api/client";
import {
  ArchetypeFolderMatrix,
  archetypeMapToPayload,
  buildArchetypePermissionMap,
  type ArchetypePermissionMap,
} from "../components/ArchetypeFolderMatrix";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { useToast } from "../components/Toast";
import { UsersSubNav } from "../components/UsersSubNav";
import type { Archetype, SharedFolder } from "../types";

export function ArchetypeFormPage() {
  const { showToast } = useToast();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [folders, setFolders] = useState<SharedFolder[]>([]);
  const [archetype, setArchetype] = useState<Archetype | null>(null);
  const [name, setName] = useState("");
  const [permissions, setPermissions] = useState<ArchetypePermissionMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const folderList = await listFolders();
      setFolders(folderList);
      if (isEdit && id) {
        const found = await getArchetype(Number(id));
        setArchetype(found);
        setName(found.name);
        const map = buildArchetypePermissionMap(folderList, found.folder_permissions);
        setPermissions(map);
      } else {
        setPermissions(Object.fromEntries(folderList.map((f) => [f.id, "none"])));
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load form.");
    } finally {
      setLoading(false);
    }
  }, [id, isEdit]);

  useEffect(() => {
    load();
  }, [load]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      let archetypeId = archetype?.id;
      if (isEdit && archetype) {
        if (!archetype.is_system && name.trim() !== archetype.name) {
          await updateArchetype(archetype.id, { name: name.trim() });
        }
      } else {
        const created = await createArchetype(name.trim());
        archetypeId = created.id;
      }
      if (archetypeId !== undefined) {
        await replaceArchetypePermissions(archetypeId, archetypeMapToPayload(permissions));
      }
      navigate("/users/archetypes");
      showToast("Archetype saved.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading…" />;

  return (
    <div className="page page-narrow">
      <UsersSubNav />
      <PageIntro
        title={isEdit ? `Edit ${archetype?.name ?? "archetype"}` : "Create archetype"}
        lede={
          isEdit && archetype?.can_view_all_personal
            ? "Super User can read all personal folders. Shared folder access is optional."
            : "Set shared folder access for everyone assigned this archetype."
        }
      />
      <ErrorBanner message={error} />
      <section className="card form-card">
        <form onSubmit={onSubmit} className="stack-form">
          <label>
            Name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={Boolean(archetype?.is_system)}
            />
            {archetype?.is_system ? (
              <span className="hint">System archetypes cannot be renamed.</span>
            ) : null}
          </label>

          {archetype?.can_view_all_personal ? (
            <p className="hint">
              This archetype can view all personal folders. That ability cannot be granted to custom
              archetypes.
            </p>
          ) : null}

          <fieldset className="permission-fieldset">
            <legend>Shared folder access</legend>
            <ArchetypeFolderMatrix
              folders={folders}
              value={permissions}
              onChange={setPermissions}
            />
          </fieldset>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Saving…" : "Save archetype"}
            </button>
            <Link to="/users/archetypes" className="btn btn-ghost">
              Cancel
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
