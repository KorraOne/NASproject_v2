import { FormEvent, useCallback, useEffect, useState } from "react";
import { listFolders } from "../api/folders";
import { createUser, deleteUser, listUsers, updateUser } from "../api/users";
import { ApiRequestError, formatBytes } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import type { FileUser, FolderAccess, SharedFolder, UserFolderPermission } from "../types";

type PermissionMap = Record<number, FolderAccess | "none">;

function emptyPermissions(folders: SharedFolder[]): PermissionMap {
  return Object.fromEntries(folders.map((f) => [f.id, "none"]));
}

function permissionsFromFolder(folders: SharedFolder[], userId: number): PermissionMap {
  const map = emptyPermissions(folders);
  for (const folder of folders) {
    const perm = folder.permissions.find((p) => p.user_id === userId);
    if (perm) map[folder.id] = perm.access;
  }
  return map;
}

function toPayload(map: PermissionMap): UserFolderPermission[] {
  return Object.entries(map)
    .filter(([, access]) => access !== "none")
    .map(([folderId, access]) => ({
      folder_id: Number(folderId),
      access: access as FolderAccess,
    }));
}

interface UserFormState {
  username: string;
  display_name: string;
  password: string;
  is_superuser: boolean;
  quota_gb: string;
  permissions: PermissionMap;
}

function defaultForm(folders: SharedFolder[]): UserFormState {
  return {
    username: "",
    display_name: "",
    password: "",
    is_superuser: false,
    quota_gb: "",
    permissions: emptyPermissions(folders),
  };
}

export function UsersPage() {
  const [users, setUsers] = useState<FileUser[]>([]);
  const [folders, setFolders] = useState<SharedFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [panel, setPanel] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<FileUser | null>(null);
  const [form, setForm] = useState<UserFormState | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [userList, folderList] = await Promise.all([listUsers(), listFolders()]);
      setUsers(userList);
      setFolders(folderList);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function openCreate() {
    setPanel("create");
    setEditing(null);
    setForm(defaultForm(folders));
  }

  function openEdit(user: FileUser) {
    setPanel("edit");
    setEditing(user);
    setForm({
      username: user.username,
      display_name: user.display_name,
      password: "",
      is_superuser: user.is_superuser,
      quota_gb: user.quota_bytes ? String(user.quota_bytes / 1024 ** 3) : "",
      permissions: permissionsFromFolder(folders, user.id),
    });
  }

  function closePanel() {
    setPanel(null);
    setEditing(null);
    setForm(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setError(null);
    try {
      const quotaBytes =
        form.quota_gb.trim() === ""
          ? null
          : Math.round(parseFloat(form.quota_gb) * 1024 ** 3);
      if (quotaBytes !== null && (Number.isNaN(quotaBytes) || quotaBytes <= 0)) {
        setError("Quota must be a positive number of gigabytes, or leave blank.");
        setBusy(false);
        return;
      }

      if (panel === "create") {
        if (form.password.length < 8) {
          setError("Password must be at least 8 characters.");
          setBusy(false);
          return;
        }
        const created = await createUser({
          username: form.username.trim().toLowerCase(),
          display_name: form.display_name.trim() || form.username.trim(),
          password: form.password,
          is_superuser: form.is_superuser,
          quota_bytes: quotaBytes,
        });
        await updateUser(created.id, { folder_permissions: toPayload(form.permissions) });
      } else if (editing) {
        const payload: Parameters<typeof updateUser>[1] = {
          display_name: form.display_name.trim(),
          is_superuser: form.is_superuser,
          quota_bytes: quotaBytes,
          folder_permissions: toPayload(form.permissions),
        };
        if (form.password) {
          if (form.password.length < 8) {
            setError("New password must be at least 8 characters.");
            setBusy(false);
            return;
          }
          payload.password = form.password;
        }
        await updateUser(editing.id, payload);
      }
      closePanel();
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(user: FileUser) {
    if (!confirm(`Delete file user "${user.username}"? This removes their private folder access.`)) {
      return;
    }
    setError(null);
    try {
      await deleteUser(user.id);
      if (editing?.id === user.id) closePanel();
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Delete failed.");
    }
  }

  if (loading) return <Loading label="Loading users…" />;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>File users</h1>
          <p className="lede">People who sign in via the helper app or File Explorer to access files.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          Add user
        </button>
      </header>

      <ErrorBanner message={error} />

      <div className="page-grid">
        <section className="card">
          {users.length === 0 ? (
            <p className="muted">No file users yet. Add someone to give them a private folder and shared access.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Display name</th>
                  <th>Super-user</th>
                  <th>Quota</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className={editing?.id === user.id ? "selected" : undefined}>
                    <td>
                      <code>{user.username}</code>
                    </td>
                    <td>{user.display_name}</td>
                    <td>{user.is_superuser ? "Yes" : "No"}</td>
                    <td>{user.quota_bytes ? formatBytes(user.quota_bytes) : "—"}</td>
                    <td className="actions">
                      <button type="button" className="btn btn-small" onClick={() => openEdit(user)}>
                        Edit
                      </button>
                      <button type="button" className="btn btn-small btn-danger" onClick={() => onDelete(user)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {panel && form && (
          <section className="card panel">
            <h2>{panel === "create" ? "Add file user" : `Edit ${editing?.username}`}</h2>
            <form onSubmit={onSubmit} className="stack-form">
              {panel === "create" && (
                <label>
                  Username
                  <input
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    required
                    pattern="[a-z][a-z0-9_]{2,31}"
                    title="Lowercase letters, digits, underscore; 3–32 characters."
                  />
                  <span className="hint">Used for sign-in and private folder name.</span>
                </label>
              )}
              <label>
                Display name
                <input
                  value={form.display_name}
                  onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                />
              </label>
              <label>
                {panel === "create" ? "Password" : "New password (optional)"}
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required={panel === "create"}
                  minLength={panel === "create" ? 8 : undefined}
                />
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.is_superuser}
                  onChange={(e) => setForm({ ...form, is_superuser: e.target.checked })}
                />
                Super-user (read-only access to all private folders)
              </label>
              <label>
                Private folder quota (GB, optional)
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={form.quota_gb}
                  onChange={(e) => setForm({ ...form, quota_gb: e.target.value })}
                />
              </label>

              <fieldset className="permission-fieldset">
                <legend>Shared folder access</legend>
                {folders.map((folder) => (
                  <label key={folder.id} className="permission-row">
                    <span>{folder.name}</span>
                    <select
                      value={form.permissions[folder.id] ?? "none"}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          permissions: {
                            ...form.permissions,
                            [folder.id]: e.target.value as FolderAccess | "none",
                          },
                        })
                      }
                    >
                      <option value="none">No access</option>
                      <option value="read">Read only</option>
                      <option value="read_write">Read & write</option>
                    </select>
                  </label>
                ))}
              </fieldset>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  {busy ? "Saving…" : "Save"}
                </button>
                <button type="button" className="btn btn-ghost" onClick={closePanel}>
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}
