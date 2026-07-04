import { apiFetch } from "./client";
import type { FileUser, UserFolderPermission } from "../types";

export function listUsers(): Promise<FileUser[]> {
  return apiFetch("/api/users");
}

export function createUser(payload: {
  username: string;
  display_name?: string;
  password: string;
  is_superuser?: boolean;
  quota_bytes?: number | null;
}): Promise<FileUser> {
  return apiFetch("/api/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUser(
  id: number,
  payload: {
    display_name?: string;
    password?: string;
    is_superuser?: boolean;
    quota_bytes?: number | null;
    folder_permissions?: UserFolderPermission[];
  },
): Promise<FileUser> {
  return apiFetch(`/api/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteUser(id: number): Promise<{ message: string }> {
  return apiFetch(`/api/users/${id}`, { method: "DELETE" });
}
