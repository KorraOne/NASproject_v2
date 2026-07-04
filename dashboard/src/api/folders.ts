import { apiFetch } from "./client";
import type { FolderAccess, FolderPermission, SharedFolder } from "../types";

export function listFolders(): Promise<SharedFolder[]> {
  return apiFetch("/api/folders");
}

export function createFolder(name: string): Promise<SharedFolder> {
  return apiFetch("/api/folders", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function renameFolder(id: number, name: string): Promise<SharedFolder> {
  return apiFetch(`/api/folders/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
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
