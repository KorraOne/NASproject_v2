import { apiFetch } from "./client";

export interface SystemInfo {
  hostname: string;
  ips: string[];
  uptime_seconds: number;
  data_mount: string;
  data_total_bytes: number;
  data_used_bytes: number;
  data_free_bytes: number;
  os_total_bytes: number;
  os_used_bytes: number;
  os_free_bytes: number;
  version: string;
  serial?: string | null;
  admin_email?: string | null;
}

export function getSystemInfo(): Promise<SystemInfo> {
  return apiFetch("/api/system/info");
}

export function getSshStatus(): Promise<{ remote_enabled: boolean }> {
  return apiFetch("/api/system/ssh");
}

export function setSshStatus(enabled: boolean): Promise<{ remote_enabled: boolean }> {
  return apiFetch("/api/system/ssh", {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
}

export function rebootAppliance(confirm: boolean): Promise<{ message: string }> {
  return apiFetch("/api/system/reboot", {
    method: "POST",
    body: JSON.stringify({ confirm }),
  });
}

export function shutdownAppliance(confirm: boolean): Promise<{ message: string }> {
  return apiFetch("/api/system/shutdown", {
    method: "POST",
    body: JSON.stringify({ confirm }),
  });
}

export interface StorageSettings {
  default_personal_quota_bytes: number | null;
}

export function getStorageSettings(): Promise<StorageSettings> {
  return apiFetch("/api/system/storage-settings");
}

export function updateStorageSettings(payload: {
  default_personal_quota_bytes: number | null;
  apply_to_uncapped_users?: boolean;
}): Promise<StorageSettings> {
  return apiFetch("/api/system/storage-settings", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export interface UpdateCheck {
  updates_enabled: boolean;
  current_version: string;
  update_available: boolean;
  available_version: string | null;
  tarball_url: string | null;
  sha256: string | null;
  notes: string | null;
}

export function checkForUpdates(): Promise<UpdateCheck> {
  return apiFetch("/api/system/updates/check");
}

export function applyLatestUpdate(): Promise<{ message: string; applying_version?: string | null }> {
  return apiFetch("/api/system/updates/apply", { method: "POST" });
}
