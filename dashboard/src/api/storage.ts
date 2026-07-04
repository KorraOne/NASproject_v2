import { apiFetch } from "./client";
import type { StorageOverview } from "../types";

export function getStorageOverview(): Promise<StorageOverview> {
  return apiFetch("/api/storage");
}
