import { apiFetch } from "./client";
import type { FolderAccess, FolderArchetypePermission, FolderPermission, SharedFolder } from "../types";

export function listFolders(): Promise<SharedFolder[]> {
  return apiFetch("/api/folders");
}

export function createFolder(
  name: string,
  options?: { quota_bytes?: number; archetype_permissions?: { archetype_id: number; access: FolderAccess }[] },
): Promise<SharedFolder> {
  return apiFetch("/api/folders", {
    method: "POST",
    body: JSON.stringify({
      name,
      quota_bytes: options?.quota_bytes ?? null,
      archetype_permissions: options?.archetype_permissions ?? [],
    }),
  });
}

export function updateFolder(
  id: number,
  updates: { name?: string; quota_bytes?: number | null },
): Promise<SharedFolder> {
  return apiFetch(`/api/folders/${id}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export function renameFolder(id: number, name: string): Promise<SharedFolder> {
  return updateFolder(id, { name });
}

export function deleteFolder(id: number): Promise<{ message: string }> {
  return apiFetch(`/api/folders/${id}`, { method: "DELETE" });
}

export function replaceFolderPermissions(
  id: number,
  permissions: { user_id: number; access: FolderAccess }[],
): Promise<FolderPermission[]> {
  return apiFetch(`/api/folders/${id}/permissions`, {
    method: "PUT",
    body: JSON.stringify({ permissions }),
  });
}

export function getFolderArchetypePermissions(id: number): Promise<FolderArchetypePermission[]> {
  return apiFetch(`/api/folders/${id}/archetype-permissions`);
}

export function replaceFolderArchetypePermissions(
  id: number,
  permissions: { archetype_id: number; access: FolderAccess }[],
): Promise<FolderArchetypePermission[]> {
  return apiFetch(`/api/folders/${id}/archetype-permissions`, {
    method: "PUT",
    body: JSON.stringify({ permissions }),
  });
}
