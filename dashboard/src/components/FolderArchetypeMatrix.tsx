import type { Archetype, FolderAccess } from "../types";
import { PermissionToggle } from "./PermissionToggle";
import type { PermissionLevel } from "../permissions";

export type FolderArchetypePermissionMap = Record<number, FolderAccess | "none">;

export function buildFolderArchetypePermissionMap(
  archetypes: Archetype[],
  permissions: { archetype_id: number; access: FolderAccess }[],
): FolderArchetypePermissionMap {
  const map: FolderArchetypePermissionMap = Object.fromEntries(
    archetypes.map((a) => [a.id, "none"]),
  );
  for (const perm of permissions) {
    map[perm.archetype_id] = perm.access;
  }
  return map;
}

export function folderArchetypeMapToPayload(
  map: FolderArchetypePermissionMap,
): { archetype_id: number; access: FolderAccess }[] {
  return Object.entries(map)
    .filter(([, access]) => access !== "none")
    .map(([archetypeId, access]) => ({
      archetype_id: Number(archetypeId),
      access: access as FolderAccess,
    }));
}

interface FolderArchetypeMatrixProps {
  archetypes: Archetype[];
  value: FolderArchetypePermissionMap;
  onChange: (next: FolderArchetypePermissionMap) => void;
}

export function FolderArchetypeMatrix({
  archetypes,
  value,
  onChange,
}: FolderArchetypeMatrixProps) {
  if (archetypes.length === 0) {
    return <p className="muted">Add archetypes first.</p>;
  }

  function setAccess(archetypeId: number, access: PermissionLevel) {
    onChange({ ...value, [archetypeId]: access });
  }

  return (
    <div className="archetype-folder-matrix folder-archetype-matrix">
      {archetypes.map((archetype) => {
        const access = value[archetype.id] ?? "none";
        return (
          <div key={archetype.id} className="archetype-folder-row">
            <div>
              <strong>{archetype.name}</strong>
              {archetype.can_view_all_personal ? (
                <p className="hint">Also views all personal folders</p>
              ) : null}
            </div>
            <PermissionToggle
              value={access}
              label={`${archetype.name} access`}
              onChange={(next) => setAccess(archetype.id, next)}
            />
          </div>
        );
      })}
    </div>
  );
}
