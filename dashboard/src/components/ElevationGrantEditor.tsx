import { useMemo, useState } from "react";
import { permissionLabel } from "../permissions";
import type {
  ElevationOptions,
  FolderAccess,
  PendingElevationGrant,
} from "../types";
import { SearchablePicker, type SearchablePickerItem } from "./SearchablePicker";

type GrantType = "shared_folder" | "personal_folder";

interface ElevationGrantEditorProps {
  grants: PendingElevationGrant[];
  options: ElevationOptions;
  totalSharedFolderCount: number;
  onChange: (grants: PendingElevationGrant[]) => void;
}

export function ElevationGrantEditor({
  grants,
  options,
  totalSharedFolderCount,
  onChange,
}: ElevationGrantEditorProps) {
  const [grantType, setGrantType] = useState<GrantType>("shared_folder");
  const [selectedTargetId, setSelectedTargetId] = useState<number | null>(null);
  const [selectedAccess, setSelectedAccess] = useState<FolderAccess | "">("");
  const [showAddPanel, setShowAddPanel] = useState(grants.length === 0);

  const grantedKeys = useMemo(
    () => new Set(grants.map((g) => `${g.grant_type}:${g.target_id}`)),
    [grants],
  );

  const sharedPickerItems: SearchablePickerItem[] = useMemo(
    () =>
      options.shared_folders
        .filter((f) => !grantedKeys.has(`shared_folder:${f.id}`))
        .map((f) => ({
          id: f.id,
          label: f.name,
          sublabel: `Archetype: ${permissionLabel(f.baseline_access)}`,
        })),
    [options.shared_folders, grantedKeys],
  );

  const personalPickerItems: SearchablePickerItem[] = useMemo(
    () =>
      options.personal_folders
        .filter((u) => !grantedKeys.has(`personal_folder:${u.user_id}`))
        .map((u) => ({
          id: u.user_id,
          label: u.display_name,
          sublabel: `Personal/${u.username}`,
        })),
    [options.personal_folders, grantedKeys],
  );

  const pickerItems = grantType === "shared_folder" ? sharedPickerItems : personalPickerItems;

  const selectedShared = options.shared_folders.find((f) => f.id === selectedTargetId);
  const selectedPersonal = options.personal_folders.find((u) => u.user_id === selectedTargetId);

  const allowedAccess =
    grantType === "shared_folder"
      ? (selectedShared?.allowed_access ?? [])
      : (selectedPersonal?.allowed_access ?? []);

  const hiddenSharedCount = totalSharedFolderCount - options.shared_folders.length;

  function onSelectTarget(id: number) {
    setSelectedTargetId(id);
    const allowed =
      grantType === "shared_folder"
        ? options.shared_folders.find((f) => f.id === id)?.allowed_access
        : options.personal_folders.find((u) => u.user_id === id)?.allowed_access;
    setSelectedAccess(allowed?.[0] ?? "");
  }

  function onAddGrant() {
    if (selectedTargetId === null || !selectedAccess) return;

    if (grantType === "shared_folder" && selectedShared) {
      onChange([
        ...grants,
        {
          grant_type: "shared_folder",
          target_id: selectedShared.id,
          target_name: selectedShared.name,
          access: selectedAccess,
          baseline_access: selectedShared.baseline_access,
        },
      ]);
    } else if (grantType === "personal_folder" && selectedPersonal) {
      onChange([
        ...grants,
        {
          grant_type: "personal_folder",
          target_id: selectedPersonal.user_id,
          target_name: `Personal/${selectedPersonal.username}`,
          access: selectedAccess,
          baseline_access: selectedPersonal.baseline_access,
        },
      ]);
    }

    setSelectedTargetId(null);
    setSelectedAccess("");
    setShowAddPanel(false);
  }

  function removeGrant(index: number) {
    onChange(grants.filter((_, i) => i !== index));
  }

  function updateGrantAccess(index: number, access: FolderAccess) {
    onChange(grants.map((g, i) => (i === index ? { ...g, access } : g)));
  }

  return (
    <div className="elevation-grant-editor">
      {grants.length > 0 ? (
        <table className="data-table elevation-grants-table">
          <thead>
            <tr>
              <th>Target</th>
              <th>Type</th>
              <th>Access</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {grants.map((grant, index) => {
              const option =
                grant.grant_type === "shared_folder"
                  ? options.shared_folders.find((f) => f.id === grant.target_id)
                  : options.personal_folders.find((u) => u.user_id === grant.target_id);
              const allowed = option?.allowed_access ?? [grant.access];

              return (
                <tr key={`${grant.grant_type}-${grant.target_id}`}>
                  <td>
                    <strong>{grant.target_name}</strong>
                    {grant.grant_type === "shared_folder" ? (
                      <p className="hint">
                        Archetype: {permissionLabel(grant.baseline_access)} →{" "}
                        {permissionLabel(grant.access)}
                      </p>
                    ) : null}
                  </td>
                  <td>
                    {grant.grant_type === "shared_folder" ? "Shared folder" : "Personal folder"}
                  </td>
                  <td>
                    <select
                      value={grant.access}
                      onChange={(e) => updateGrantAccess(index, e.target.value as FolderAccess)}
                    >
                      {allowed.map((level) => (
                        <option key={level} value={level}>
                          {permissionLabel(level)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-small btn-ghost"
                      onClick={() => removeGrant(index)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <p className="hint">No temporary grants yet. Add access below.</p>
      )}

      {!showAddPanel ? (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => setShowAddPanel(true)}
          disabled={sharedPickerItems.length === 0 && personalPickerItems.length === 0}
        >
          Add access
        </button>
      ) : (
        <fieldset className="permission-fieldset elevation-add-panel">
          <legend>Add temporary access</legend>

          <div className="segmented-control" role="group" aria-label="Grant type">
            <button
              type="button"
              className={grantType === "shared_folder" ? "active" : undefined}
              onClick={() => {
                setGrantType("shared_folder");
                setSelectedTargetId(null);
                setSelectedAccess("");
              }}
            >
              Shared folder
            </button>
            <button
              type="button"
              className={grantType === "personal_folder" ? "active" : undefined}
              onClick={() => {
                setGrantType("personal_folder");
                setSelectedTargetId(null);
                setSelectedAccess("");
              }}
            >
              Personal folder
            </button>
          </div>

          {grantType === "shared_folder" && sharedPickerItems.length === 0 ? (
            <p className="hint">
              All shared folders are already covered by this person&apos;s archetype, or all
              eligible folders are in the list above.
            </p>
          ) : grantType === "personal_folder" && personalPickerItems.length === 0 ? (
            <p className="hint">No other file users available.</p>
          ) : (
            <>
              <SearchablePicker
                items={pickerItems}
                selectedId={selectedTargetId}
                onSelect={onSelectTarget}
                placeholder={
                  grantType === "shared_folder" ? "Search shared folders…" : "Search people…"
                }
                emptyMessage="No matches."
              />

              {selectedTargetId !== null && allowedAccess.length > 0 ? (
                <label>
                  Temporary access level
                  <select
                    value={selectedAccess}
                    onChange={(e) => setSelectedAccess(e.target.value as FolderAccess)}
                  >
                    {allowedAccess.map((level) => (
                      <option key={level} value={level}>
                        {permissionLabel(level)}
                      </option>
                    ))}
                  </select>
                  {grantType === "shared_folder" && selectedShared ? (
                    <span className="hint">
                      Archetype access: {permissionLabel(selectedShared.baseline_access)} → granting{" "}
                      {permissionLabel((selectedAccess || allowedAccess[0]) as FolderAccess)}
                    </span>
                  ) : null}
                </label>
              ) : null}

              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={selectedTargetId === null || !selectedAccess}
                  onClick={onAddGrant}
                >
                  Add to list
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowAddPanel(false);
                    setSelectedTargetId(null);
                    setSelectedAccess("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </fieldset>
      )}

      {hiddenSharedCount > 0 ? (
        <p className="hint">
          {hiddenSharedCount} shared folder{hiddenSharedCount === 1 ? "" : "s"} hidden — already at
          full access via archetype.
        </p>
      ) : null}
    </div>
  );
}
