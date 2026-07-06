export interface SetupStatus {
  setup_complete: boolean;
  requires_claim_code?: boolean;
}

export type FolderAccess = "read" | "read_write";
export type PermissionLevel = FolderAccess | "none";

export interface ElevationGrant {
  grant_type: "shared_folder" | "personal_folder";
  target_id: number;
  target_name: string;
  access: FolderAccess;
}

export interface ElevationSharedFolderOption {
  id: number;
  name: string;
  baseline_access: PermissionLevel;
  allowed_access: FolderAccess[];
}

export interface ElevationPersonalFolderOption {
  user_id: number;
  username: string;
  display_name: string;
  baseline_access: PermissionLevel;
  allowed_access: FolderAccess[];
}

export interface ElevationOptions {
  shared_folders: ElevationSharedFolderOption[];
  personal_folders: ElevationPersonalFolderOption[];
}

export interface PendingElevationGrant {
  grant_type: "shared_folder" | "personal_folder";
  target_id: number;
  target_name: string;
  access: FolderAccess;
  baseline_access: PermissionLevel;
}

export interface UserElevation {
  expires_at: string;
  granted_at: string;
  reason: string | null;
  grants: ElevationGrant[];
}

export interface FileUser {
  id: number;
  username: string;
  display_name: string;
  archetype_id: number | null;
  archetype_name: string | null;
  is_superuser: boolean;
  is_elevated: boolean;
  elevation: UserElevation | null;
  quota_bytes: number | null;
  created_at: string;
  updated_at: string;
}

export interface ArchetypeFolderPermission {
  folder_id: number;
  folder_name: string;
  access: FolderAccess;
}

export interface Archetype {
  id: number;
  name: string;
  is_system: boolean;
  can_view_all_personal: boolean;
  user_count: number;
  created_at: string;
  folder_permissions: ArchetypeFolderPermission[];
}

export interface EffectivePermission {
  user_id: number;
  username: string;
  display_name: string;
  archetype_id: number | null;
  archetype_name: string | null;
  can_view_all_personal: boolean;
  is_elevated: boolean;
  elevation: UserElevation | null;
  personal_folder: string;
  shared_folders: { folder_name: string; access: FolderAccess }[];
}

export interface FolderPermission {
  user_id: number;
  username: string;
  access: "read" | "read_write";
}

export interface SharedFolder {
  id: number;
  name: string;
  slug: string;
  path: string;
  share_name: string;
  quota_bytes: number | null;
  created_at: string;
  permissions: FolderPermission[];
}

export interface StorageOverview {
  mount: string;
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  file_user_count: number;
  shared_folder_count: number;
}

export interface SnapshotSettings {
  snapshot_hour: number;
  retention_daily: number;
  retention_weekly: number;
  retention_monthly: number;
}

export interface SnapshotBrowseEntry {
  name: string;
  path: string;
  is_dir: boolean;
}

export interface FolderArchetypePermission {
  archetype_id: number;
  archetype_name: string;
  access: FolderAccess;
}

export interface UserFolderPermission {
  folder_id: number;
  access: FolderAccess;
}

export interface ApiError {
  detail: string;
}
