import { apiFetch } from "./client";

export interface PublicInfo {
  hostname: string;
  primary_ip: string | null;
  ips: string[];
  version: string;
  help_path: string;
}

export function getPublicInfo(): Promise<PublicInfo> {
  return apiFetch("/api/public/info");
}
