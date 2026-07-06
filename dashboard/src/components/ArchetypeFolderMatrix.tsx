import type { FolderAccess, SharedFolder } from "../types";
import { PermissionToggle } from "./PermissionToggle";
import type { PermissionLevel } from "../permissions";

export type ArchetypePermissionMap = Record<number, FolderAccess | "none">;

export function buildArchetypePermissionMap(
  folders: SharedFolder[],
  permissions: { folder_id: number; access: FolderAccess }[],
): ArchetypePermissionMap {
  const map: ArchetypePermissionMap = Object.fromEntries(folders.map((f) => [f.id, "none"]));
  for (const perm of permissions) {
    map[perm.folder_id] = perm.access;
  }
  return map;
}

export function archetypeMapToPayload(
  map: ArchetypePermissionMap,
): { folder_id: number; access: FolderAccess }[] {
  return Object.entries(map)
    .filter(([, access]) => access !== "none")
    .map(([folderId, access]) => ({
      folder_id: Number(folderId),
      access: access as FolderAccess,
    }));
}

interface ArchetypeFolderMatrixProps {
  folders: SharedFolder[];
  value: ArchetypePermissionMap;
  onChange: (next: ArchetypePermissionMap) => void;
}

export function ArchetypeFolderMatrix({ folders, value, onChange }: ArchetypeFolderMatrixProps) {
  if (folders.length === 0) {
    return <p className="muted">Add shared folders first.</p>;
  }

  function setAccess(folderId: number, access: PermissionLevel) {
    onChange({ ...value, [folderId]: access });
  }

  return (
    <div className="archetype-folder-matrix">
      {folders.map((folder) => {
        const access = value[folder.id] ?? "none";
        return (
          <div key={folder.id} className="archetype-folder-row">
            <strong>{folder.name}</strong>
            <PermissionToggle
              value={access}
              label={`Access to ${folder.name}`}
              onChange={(next) => setAccess(folder.id, next)}
            />
          </div>
        );
      })}
    </div>
  );
}
