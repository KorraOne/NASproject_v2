import { apiFetch, setToken } from "./client";

export function login(email: string | undefined, password: string): Promise<{ access_token: string }> {
  const body: { password: string; email?: string } = { password };
  if (email?.trim()) {
    body.email = email.trim();
  }
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  }, false);
}

export async function signIn(email: string | undefined, password: string): Promise<void> {
  const result = await login(email, password);
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

export function getMe(): Promise<{ role: string; email?: string | null }> {
  return apiFetch("/api/auth/me");
}
