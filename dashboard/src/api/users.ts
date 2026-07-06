import { apiFetch } from "./client";
import type { ElevationOptions, FileUser, FolderAccess, UserElevation } from "../types";

export function listUsers(): Promise<FileUser[]> {
  return apiFetch("/api/users");
}

export function getUser(id: number): Promise<FileUser> {
  return apiFetch(`/api/users/${id}`);
}

export function getElevationOptions(id: number): Promise<ElevationOptions> {
  return apiFetch(`/api/users/${id}/elevation/options`);
}

export function createUser(payload: {
  username: string;
  display_name?: string;
  password: string;
  archetype_id?: number;
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
    archetype_id?: number;
    quota_bytes?: number | null;
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

export function replaceElevation(
  id: number,
  payload: {
    duration_hours: number;
    reason?: string;
    grants: Array<{
      grant_type: "shared_folder" | "personal_folder";
      target_id: number;
      access: FolderAccess;
    }>;
  },
): Promise<UserElevation> {
  return apiFetch(`/api/users/${id}/elevation`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function revokeElevation(id: number): Promise<{ message: string }> {
  return apiFetch(`/api/users/${id}/elevation`, { method: "DELETE" });
}
