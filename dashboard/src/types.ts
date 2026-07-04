export interface SetupStatus {
  setup_complete: boolean;
}

export interface FileUser {
  id: number;
  username: string;
  display_name: string;
  is_superuser: boolean;
  quota_bytes: number | null;
  created_at: string;
  updated_at: string;
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

export type FolderAccess = "read" | "read_write";

export interface UserFolderPermission {
  folder_id: number;
  access: FolderAccess;
}

export interface ApiError {
  detail: string;
}
