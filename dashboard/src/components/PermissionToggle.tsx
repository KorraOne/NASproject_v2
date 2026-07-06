import type { FolderAccess } from "../types";
import { PERMISSION_OPTIONS, type PermissionLevel } from "../permissions";

interface PermissionToggleProps {
  value: PermissionLevel;
  onChange: (next: PermissionLevel) => void;
  label: string;
  compact?: boolean;
}

export function PermissionToggle({ value, onChange, label, compact }: PermissionToggleProps) {
  return (
    <div
      className={`perm-toggle${compact ? " perm-toggle-compact" : ""}`}
      role="group"
      aria-label={label}
    >
      {PERMISSION_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={`perm-toggle-btn perm-${option.value}${value === option.value ? " active" : ""}`}
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value as FolderAccess | "none")}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
