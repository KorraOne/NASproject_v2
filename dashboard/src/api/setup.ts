import { apiFetch } from "./client";
import type { SetupStatus } from "../types";

export function getSetupStatus(): Promise<SetupStatus> {
  return apiFetch<SetupStatus>("/api/setup/status", {}, false);
}

export function completeSetup(password: string, timezone: string): Promise<{ message: string }> {
  return apiFetch("/api/setup", {
    method: "POST",
    body: JSON.stringify({ password, timezone }),
  }, false);
}
