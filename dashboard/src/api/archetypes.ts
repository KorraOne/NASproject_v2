import { apiFetch } from "./client";
import type { Archetype, FolderAccess } from "../types";

export function listArchetypes(): Promise<Archetype[]> {
  return apiFetch("/api/archetypes");
}

export function getArchetype(id: number): Promise<Archetype> {
  return apiFetch(`/api/archetypes/${id}`);
}

export function createArchetype(name: string): Promise<Archetype> {
  return apiFetch("/api/archetypes", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function updateArchetype(id: number, payload: { name?: string }): Promise<Archetype> {
  return apiFetch(`/api/archetypes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteArchetype(id: number): Promise<{ message: string }> {
  return apiFetch(`/api/archetypes/${id}`, { method: "DELETE" });
}

export function replaceArchetypePermissions(
  id: number,
  permissions: { folder_id: number; access: FolderAccess }[],
): Promise<Archetype["folder_permissions"]> {
  return apiFetch(`/api/archetypes/${id}/permissions`, {
    method: "PUT",
    body: JSON.stringify({ permissions }),
  });
}
