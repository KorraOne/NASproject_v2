import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createFolder,
  deleteFolder,
  listFolders,
  renameFolder,
  replaceFolderPermissions,
} from "../api/folders";
import { listUsers } from "../api/users";
import { ApiRequestError } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import type { FileUser, FolderAccess, SharedFolder } from "../types";

type UserAccessMap = Record<number, FolderAccess | "none">;

function emptyAccess(users: FileUser[]): UserAccessMap {
  return Object.fromEntries(users.map((u) => [u.id, "none"]));
}

function accessFromFolder(folder: SharedFolder, users: FileUser[]): UserAccessMap {
  const map = emptyAccess(users);
  for (const perm of folder.permissions) {
    map[perm.user_id] = perm.access;
  }
  return map;
}

export function FoldersPage() {
  const [folders, setFolders] = useState<SharedFolder[]>([]);
  const [users, setUsers] = useState<FileUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SharedFolder | null>(null);
  const [newName, setNewName] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [accessMap, setAccessMap] = useState<UserAccessMap>({});
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [folderList, userList] = await Promise.all([listFolders(), listUsers()]);
      setFolders(folderList);
      setUsers(userList);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load folders.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function selectFolder(folder: SharedFolder) {
    setSelected(folder);
    setRenameValue(folder.name);
    setAccessMap(accessFromFolder(folder, users));
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createFolder(name);
      setNewName("");
      setCreating(false);
      await load();
      setSelected(created);
      setRenameValue(created.name);
      setAccessMap(emptyAccess(users));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not create folder.");
    } finally {
      setBusy(false);
    }
  }

  async function onSavePermissions(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const permissions = Object.entries(accessMap)
        .filter(([, access]) => access !== "none")
        .map(([userId, access]) => ({
          user_id: Number(userId),
          access: access as FolderAccess,
        }));
      await replaceFolderPermissions(selected.id, permissions);
      if (renameValue.trim() && renameValue.trim() !== selected.name) {
        await renameFolder(selected.id, renameValue.trim());
      }
      await load();
      const refreshed = (await listFolders()).find((f) => f.id === selected.id);
      if (refreshed) selectFolder(refreshed);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(folder: SharedFolder) {
    if (!confirm(`Delete shared folder "${folder.name}"? It must be empty.`)) return;
    setError(null);
    try {
      await deleteFolder(folder.id);
      if (selected?.id === folder.id) setSelected(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Delete failed.");
    }
  }

  if (loading) return <Loading label="Loading folders…" />;

  return (
    <div className="page">
      <PageIntro
        title="Shared folders"
        lede="Folders your team can open together — like Projects or Invoices."
        action={
          <button type="button" className="btn btn-primary" onClick={() => setCreating((v) => !v)}>
            {creating ? "Cancel" : "Add folder"}
          </button>
        }
      />

      <ErrorBanner message={error} />

      {creating && (
        <section className="card inline-form">
          <form onSubmit={onCreate} className="inline-form-row">
            <label>
              Folder name
              <input value={newName} onChange={(e) => setNewName(e.target.value)} required />
            </label>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Create
            </button>
          </form>
        </section>
      )}

      <div className="page-grid">
        <section className="card">
          {folders.length === 0 ? (
            <p className="muted">No shared folders yet.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Share name</th>
                  <th>People with access</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {folders.map((folder) => (
                  <tr
                    key={folder.id}
                    className={selected?.id === folder.id ? "selected" : undefined}
                  >
                    <td>{folder.name}</td>
                    <td>
                      <code>{folder.share_name}</code>
                    </td>
                    <td>{folder.permissions.length}</td>
                    <td className="actions">
                      <button type="button" className="btn btn-small" onClick={() => selectFolder(folder)}>
                        Edit
                      </button>
                      <button type="button" className="btn btn-small btn-danger" onClick={() => onDelete(folder)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {selected && (
          <section className="card panel">
            <h2>{selected.name}</h2>
            <form onSubmit={onSavePermissions} className="stack-form">
              <label>
                Folder name
                <input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} required />
              </label>

              <fieldset className="permission-fieldset">
                <legend>Who can access this folder</legend>
                {users.length === 0 ? (
                  <p className="muted">Add file users first, then assign access here.</p>
                ) : (
                  users.map((user) => (
                    <label key={user.id} className="permission-row">
                      <span>
                        {user.display_name} <code>({user.username})</code>
                      </span>
                      <select
                        value={accessMap[user.id] ?? "none"}
                        onChange={(e) =>
                          setAccessMap({
                            ...accessMap,
                            [user.id]: e.target.value as FolderAccess | "none",
                          })
                        }
                      >
                        <option value="none">No access</option>
                        <option value="read">Read only</option>
                        <option value="read_write">Read & write</option>
                      </select>
                    </label>
                  ))
                )}
              </fieldset>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  {busy ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}
