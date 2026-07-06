import type { FolderAccess } from "./types";

export type PermissionLevel = FolderAccess | "none";

export const PERMISSION_OPTIONS: { value: PermissionLevel; label: string }[] = [
  { value: "none", label: "None" },
  { value: "read", label: "Read only" },
  { value: "read_write", label: "Read & write" },
];

export function permissionLabel(access: PermissionLevel): string {
  return PERMISSION_OPTIONS.find((o) => o.value === access)?.label ?? "None";
}
