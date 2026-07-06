import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listFolders } from "../api/folders";
import {
  getElevationOptions,
  getUser,
  replaceElevation,
  revokeElevation,
} from "../api/users";
import { ApiRequestError } from "../api/client";
import { ElevationGrantEditor } from "../components/ElevationGrantEditor";
import { ErrorBanner } from "../components/ErrorBanner";
import { Loading } from "../components/Loading";
import { PageIntro } from "../components/PageIntro";
import { UsersSubNav } from "../components/UsersSubNav";
import { useToast } from "../components/Toast";
import type { ElevationOptions, FileUser, PendingElevationGrant } from "../types";

function formatExpiry(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function grantsFromUser(user: FileUser, opts: ElevationOptions): PendingElevationGrant[] {
  return (user.elevation?.grants ?? []).map((grant) => {
    if (grant.grant_type === "shared_folder") {
      const folder = opts.shared_folders.find((f) => f.id === grant.target_id);
      return {
        grant_type: grant.grant_type,
        target_id: grant.target_id,
        target_name: grant.target_name,
        access: grant.access,
        baseline_access: folder?.baseline_access ?? "none",
      };
    }
    return {
      grant_type: grant.grant_type,
      target_id: grant.target_id,
      target_name: grant.target_name,
      access: grant.access,
      baseline_access: "none",
    };
  });
}

export function TemporaryAccessPage() {
  const { id } = useParams();
  const userId = Number(id);
  const { showToast } = useToast();
  const [user, setUser] = useState<FileUser | null>(null);
  const [options, setOptions] = useState<ElevationOptions | null>(null);
  const [totalSharedFolderCount, setTotalSharedFolderCount] = useState(0);
  const [grants, setGrants] = useState<PendingElevationGrant[]>([]);
  const [durationHours, setDurationHours] = useState("8");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!id || Number.isNaN(userId)) {
      setError("User not found.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [found, opts, folders] = await Promise.all([
        getUser(userId),
        getElevationOptions(userId),
        listFolders(),
      ]);
      setUser(found);
      setOptions(opts);
      setTotalSharedFolderCount(folders.length);
      setGrants(grantsFromUser(found, opts));
      setReason(found.elevation?.reason ?? "");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load temporary access.");
    } finally {
      setLoading(false);
    }
  }, [id, userId]);

  useEffect(() => {
    load();
  }, [load]);

  async function onSave() {
    if (!user) return;
    if (grants.length === 0) {
      setError("Add at least one folder or personal folder to grant access to.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await replaceElevation(user.id, {
        duration_hours: Number(durationHours),
        reason: reason.trim() || undefined,
        grants: grants.map((g) => ({
          grant_type: g.grant_type,
          target_id: g.target_id,
          access: g.access,
        })),
      });
      showToast("Temporary access saved.");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not save temporary access.");
    } finally {
      setBusy(false);
    }
  }

  async function onRevoke() {
    if (!user) return;
    setBusy(true);
    setError(null);
    try {
      await revokeElevation(user.id);
      showToast("Temporary access revoked.");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not revoke temporary access.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading temporary access…" />;

  if (!user) {
    return (
      <div className="page page-narrow">
        <UsersSubNav />
        <ErrorBanner message={error ?? "User not found."} />
        <Link to="/users" className="btn btn-ghost">
          Back to People
        </Link>
      </div>
    );
  }

  const isSuperUser = user.archetype_name === "Super User" || user.is_superuser;

  return (
    <div className="page page-narrow">
      <UsersSubNav />
      <PageIntro
        title={`Temporary access — ${user.display_name}`}
        lede={`Time-limited access above what the ${user.archetype_name ?? "archetype"} template provides.`}
      />
      <p className="hint page-narrow-hint">
        <Link to={`/users/${user.id}/edit`}>Edit user profile</Link>
      </p>
      <ErrorBanner message={error} />

      {isSuperUser ? (
        <section className="card section-card">
          <p className="hint">
            Super User already has full access. Temporary grants are not needed.
          </p>
        </section>
      ) : (
        <section className="card form-card">
          {user.elevation ? (
            <div className="info-banner elevation-active">
              <strong>Active until {formatExpiry(user.elevation.expires_at)}</strong>
              {user.elevation.reason ? <p className="hint">{user.elevation.reason}</p> : null}
            </div>
          ) : null}

          {options ? (
            <ElevationGrantEditor
              grants={grants}
              options={options}
              totalSharedFolderCount={totalSharedFolderCount}
              onChange={setGrants}
            />
          ) : null}

          <div className="stack-form elevation-session-fields">
            <label>
              Duration
              <select value={durationHours} onChange={(e) => setDurationHours(e.target.value)}>
                <option value="1">1 hour</option>
                <option value="4">4 hours</option>
                <option value="8">8 hours</option>
                <option value="24">1 day</option>
                <option value="72">3 days</option>
                <option value="168">1 week</option>
              </select>
            </label>
            <label>
              Reason (optional)
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Covering for Sarah while she's away"
              />
            </label>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-primary" disabled={busy} onClick={onSave}>
              {busy ? "Saving…" : user.elevation ? "Update temporary access" : "Grant temporary access"}
            </button>
            {user.elevation ? (
              <button type="button" className="btn btn-ghost" disabled={busy} onClick={onRevoke}>
                Revoke all
              </button>
            ) : null}
            <Link to="/users" className="btn btn-ghost">
              Back to People
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
