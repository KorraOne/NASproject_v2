import { apiFetch, setToken } from "./client";

export function login(password: string): Promise<{ access_token: string }> {
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ password }),
  }, false);
}

export async function signIn(password: string): Promise<void> {
  const result = await login(password);
  setToken(result.access_token);
}

export function logout(): Promise<{ message: string }> {
  return apiFetch("/api/auth/logout", { method: "POST" });
}

export async function signOut(): Promise<void> {
  try {
    await logout();
  } finally {
    setToken(null);
  }
}

export function getMe(): Promise<{ role: string }> {
  return apiFetch("/api/auth/me");
}
