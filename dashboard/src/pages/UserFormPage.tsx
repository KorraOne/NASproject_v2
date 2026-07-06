import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { listArchetypes } from "../api/archetypes";
import { listFolders } from "../api/folders";
import { createUser, listUsers, updateUser } from "../api/users";
import { ApiRequestError } from "../api/client";
import { buildArchetypePermissionMap } from "../components/ArchetypeFolderMatrix";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { UsersSubNav } from "../components/UsersSubNav";
import { PERMISSION_OPTIONS } from "../permissions";
import type { Archetype, FileUser, SharedFolder } from "../types";

function formatExpiry(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function UserFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [folders, setFolders] = useState<SharedFolder[]>([]);
  const [user, setUser] = useState<FileUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [archetypeId, setArchetypeId] = useState<number | "">("");

  const selectedArchetype = archetypes.find((a) => a.id === archetypeId) ?? null;
  const inheritedPermissions =
    selectedArchetype && folders.length > 0
      ? buildArchetypePermissionMap(folders, selectedArchetype.folder_permissions)
      : {};

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [archetypeList, folderList, userList] = await Promise.all([
        listArchetypes(),
        listFolders(),
        listUsers(),
      ]);
      setArchetypes(archetypeList);
      setFolders(folderList);
      const standard = archetypeList.find((a) => a.name === "Standard Employee");
      if (isEdit && id) {
        const found = userList.find((u) => u.id === Number(id));
        if (!found) {
          setError("User not found.");
          return;
        }
        setUser(found);
        setUsername(found.username);
        setDisplayName(found.display_name);
        setArchetypeId(found.archetype_id ?? standard?.id ?? "");
      } else {
        setArchetypeId(standard?.id ?? archetypeList[0]?.id ?? "");
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
    if (archetypeId === "") {
      setError("Choose an archetype.");
      return;
    }
    setBusy(true);
    setError(null);

    try {
      if (isEdit && user) {
        if (password && password.length < 8) {
          setError("New password must be at least 8 characters.");
          setBusy(false);
          return;
        }
        await updateUser(user.id, {
          display_name: displayName.trim(),
          archetype_id: Number(archetypeId),
          ...(password ? { password } : {}),
        });
      } else {
        if (password.length < 8) {
          setError("Password must be at least 8 characters.");
          setBusy(false);
          return;
        }
        await createUser({
          username: username.trim().toLowerCase(),
          display_name: displayName.trim() || username.trim(),
          password,
          archetype_id: Number(archetypeId),
        });
      }
      navigate("/users");
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
        title={isEdit ? `Edit ${user?.username ?? "user"}` : "Add file user"}
        lede={
          isEdit
            ? "Update account details and archetype assignment."
            : "Create a sign-in for someone who needs their own private folder."
        }
      />
      <ErrorBanner message={error} />
      <section className="card form-card">
        <form onSubmit={onSubmit} className="stack-form">
          {!isEdit && (
            <label>
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                pattern="[a-z][a-z0-9_]{2,31}"
              />
              <span className="hint">Lowercase letters, digits, underscore; 3–32 characters.</span>
            </label>
          )}
          <label>
            Display name
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
          <label>
            {isEdit ? "New password (optional)" : "Password"}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required={!isEdit}
              minLength={isEdit ? undefined : 8}
            />
          </label>
          <label>
            Archetype
            <select
              value={archetypeId}
              onChange={(e) => setArchetypeId(Number(e.target.value))}
              required
            >
              {archetypes.map((archetype) => (
                <option key={archetype.id} value={archetype.id}>
                  {archetype.name}
                  {archetype.can_view_all_personal ? " (all personal folders)" : ""}
                </option>
              ))}
            </select>
            <span className="hint">
              <Link to="/users/archetypes">Edit archetypes</Link> to change shared folder templates.
            </span>
          </label>

          {selectedArchetype && folders.length > 0 ? (
            <fieldset className="permission-fieldset">
              <legend>Inherited shared folder access</legend>
              <dl className="stat-list">
                {folders.map((folder) => {
                  const access = inheritedPermissions[folder.id] ?? "none";
                  const label =
                    PERMISSION_OPTIONS.find((opt) => opt.value === access)?.label ?? "None";
                  return (
                    <div key={folder.id}>
                      <dt>{folder.name}</dt>
                      <dd>{label}</dd>
                    </div>
                  );
                })}
              </dl>
              <p className="hint">
                From the <strong>{selectedArchetype.name}</strong> archetype.{" "}
                <Link to={`/users/archetypes/${selectedArchetype.id}/edit`}>Edit archetype</Link>
              </p>
            </fieldset>
          ) : null}

          {isEdit && user && user.archetype_name !== "Super User" ? (
            <div className="info-banner elevation-summary">
              {user.elevation ? (
                <p>
                  Temporary access until <strong>{formatExpiry(user.elevation.expires_at)}</strong>{" "}
                  ({user.elevation.grants.length} grant
                  {user.elevation.grants.length === 1 ? "" : "s"}).{" "}
                  <Link to={`/users/${user.id}/temporary-access`}>Manage temporary access</Link>
                </p>
              ) : (
                <p>
                  Need time-limited access above their archetype?{" "}
                  <Link to={`/users/${user.id}/temporary-access`}>Grant temporary access</Link>
                </p>
              )}
            </div>
          ) : null}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Saving…" : "Save user"}
            </button>
            <Link to="/users" className="btn btn-ghost">
              Cancel
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
