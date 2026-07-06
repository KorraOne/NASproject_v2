import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { listArchetypes } from "../api/archetypes";
import {
  createFolder,
  getFolderArchetypePermissions,
  listFolders,
  replaceFolderArchetypePermissions,
  updateFolder,
} from "../api/folders";
import { ApiRequestError } from "../api/client";
import {
  buildFolderArchetypePermissionMap,
  folderArchetypeMapToPayload,
  FolderArchetypeMatrix,
  type FolderArchetypePermissionMap,
} from "../components/FolderArchetypeMatrix";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import type { Archetype } from "../types";

function gbFromBytes(bytes: number | null): string {
  if (bytes == null) return "";
  return String(Math.round((bytes / 1024 ** 3) * 10) / 10);
}

export function FolderFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");
  const [quotaGb, setQuotaGb] = useState("");
  const [archetypeMatrix, setArchetypeMatrix] = useState<FolderArchetypePermissionMap>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const archetypeList = await listArchetypes();
      setArchetypes(archetypeList);
      const emptyMap = buildFolderArchetypePermissionMap(archetypeList, []);
      if (!isEdit || !id) {
        setArchetypeMatrix(emptyMap);
        setLoading(false);
        return;
      }
      const [folders, folderPerms] = await Promise.all([
        listFolders(),
        getFolderArchetypePermissions(Number(id)),
      ]);
      const folder = folders.find((f) => f.id === Number(id));
      if (!folder) {
        setError("Folder not found.");
        return;
      }
      setName(folder.name);
      setQuotaGb(gbFromBytes(folder.quota_bytes));
      setArchetypeMatrix(
        buildFolderArchetypePermissionMap(
          archetypeList,
          folderPerms.map((p) => ({ archetype_id: p.archetype_id, access: p.access })),
        ),
      );
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load folder.");
    } finally {
      setLoading(false);
    }
  }, [id, isEdit]);

  useEffect(() => {
    load();
  }, [load]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setBusy(true);
    setError(null);
    const quotaBytes = quotaGb.trim() ? Math.round(parseFloat(quotaGb) * 1024 ** 3) : null;
    if (quotaBytes !== null && (Number.isNaN(quotaBytes) || quotaBytes <= 0)) {
      setError("Maximum folder size must be a positive number of gigabytes, or leave blank for no limit.");
      setBusy(false);
      return;
    }

    const archetypePermissions = folderArchetypeMapToPayload(archetypeMatrix);

    try {
      if (isEdit && id) {
        await updateFolder(Number(id), { name: trimmed, quota_bytes: quotaBytes });
        await replaceFolderArchetypePermissions(Number(id), archetypePermissions);
      } else {
        await createFolder(trimmed, {
          quota_bytes: quotaBytes ?? undefined,
          archetype_permissions: archetypePermissions,
        });
      }
      navigate("/folders");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading…" />;

  return (
    <div className="page page-narrow">
      <PageIntro
        title={isEdit ? "Edit folder" : "Add shared folder"}
        lede={
          isEdit
            ? "Rename the folder, adjust limits, or change which archetypes can access it."
            : "Team folders appear on drive W: for people you grant access."
        }
      />
      <ErrorBanner message={error} />
      <section className="card form-card">
        <form onSubmit={onSubmit} className="stack-form">
          <label>
            Folder name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>

          <details className="folder-details">
            <summary>Folder size limit (optional)</summary>
            <div className="folder-details-body">
              <label>
                Maximum folder size (GB)
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={quotaGb}
                  onChange={(e) => setQuotaGb(e.target.value)}
                  placeholder="No limit"
                />
                <span className="hint">
                  Caps how large this folder can grow on W:. Leave blank for unlimited capacity.
                </span>
              </label>
            </div>
          </details>

          <details className="folder-details" open={!isEdit}>
            <summary>Who can access this folder</summary>
            <div className="folder-details-body">
              <p className="hint section-card-lede">
                Set access per archetype. Everyone assigned an archetype inherits these permissions.
              </p>
              <FolderArchetypeMatrix
                archetypes={archetypes}
                value={archetypeMatrix}
                onChange={setArchetypeMatrix}
              />
              {isEdit ? (
                <p className="hint">
                  You can also edit on the <Link to="/permissions">Permissions</Link> page (By folder
                  tab).
                </p>
              ) : null}
            </div>
          </details>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Saving…" : isEdit ? "Save changes" : "Create folder"}
            </button>
            <Link to="/folders" className="btn btn-ghost">
              Cancel
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
