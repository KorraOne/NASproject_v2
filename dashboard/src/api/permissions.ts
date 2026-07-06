import { apiFetch } from "./client";
import type { EffectivePermission } from "../types";

export function listEffectivePermissions(): Promise<EffectivePermission[]> {
  return apiFetch("/api/permissions/effective");
}
