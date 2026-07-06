import { apiFetch, setToken } from "./client";
import type { SetupStatus } from "../types";

export interface SetupPayload {
  password: string;
  timezone: string;
  claim_code?: string;
  email?: string;
  backup_email?: string;
  backup_phone?: string;
}

export interface SetupResult {
  message: string;
  access_token?: string;
}

export function getSetupStatus(): Promise<SetupStatus> {
  return apiFetch<SetupStatus>("/api/setup/status", {}, false);
}

export async function completeSetup(payload: SetupPayload): Promise<SetupResult> {
  const result = await apiFetch<SetupResult>("/api/setup", {
    method: "POST",
    body: JSON.stringify(payload),
  }, false);
  if (result.access_token) {
    setToken(result.access_token);
  }
  return result;
}
