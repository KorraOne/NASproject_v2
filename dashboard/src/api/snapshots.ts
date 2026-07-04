import { apiFetch } from "./client";
import type { SnapshotBrowseEntry, SnapshotSettings } from "../types";

export interface Snapshot {
  id: string;
  name: string;
  kind: string;
  snapshot_date: string;
  created_at: string;
}

export function listSnapshots(): Promise<Snapshot[]> {
  return apiFetch("/api/snapshots");
}

export function createSnapshot(): Promise<Snapshot> {
  return apiFetch("/api/snapshots", { method: "POST" });
}

export function getSnapshotSettings(): Promise<SnapshotSettings> {
  return apiFetch("/api/snapshots/settings");
}

export function updateSnapshotSettings(
  payload: Partial<SnapshotSettings>,
): Promise<SnapshotSettings> {
  return apiFetch("/api/snapshots/settings", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function browseSnapshot(id: string, path = ""): Promise<SnapshotBrowseEntry[]> {
  const query = path ? `?path=${encodeURIComponent(path)}` : "";
  return apiFetch(`/api/snapshots/${encodeURIComponent(id)}/browse${query}`);
}

export function getRestoreToken(
  id: string,
  path: string,
): Promise<{ confirm_token: string; source_path: string }> {
  return apiFetch(
    `/api/snapshots/${encodeURIComponent(id)}/restore-token?path=${encodeURIComponent(path)}`,
  );
}

export function restoreSnapshot(
  id: string,
  source_path: string,
  confirm_token: string,
): Promise<{ message: string }> {
  return apiFetch(`/api/snapshots/${encodeURIComponent(id)}/restore`, {
    method: "POST",
    body: JSON.stringify({ source_path, confirm_token }),
  });
}
