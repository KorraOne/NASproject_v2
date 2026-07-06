import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getMe, signIn, signOut } from "../api/auth";
import { getSetupStatus } from "../api/setup";
import { ApiRequestError, getToken, setToken } from "../api/client";

type AuthState = "loading" | "needs-setup" | "needs-login" | "authenticated";

interface AuthContextValue {
  state: AuthState;
  refresh: () => Promise<void>;
  login: (password: string, email?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>("loading");

  const refresh = useCallback(async () => {
    const status = await getSetupStatus();
    if (!status.setup_complete) {
      setState("needs-setup");
      return;
    }
    const token = getToken();
    if (!token) {
      setState("needs-login");
      return;
    }
    try {
      await getMe();
      setState("authenticated");
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        setToken(null);
        setState("needs-login");
        return;
      }
      throw err;
    }
  }, []);

  useEffect(() => {
    refresh().catch(() => setState("needs-login"));
  }, [refresh]);

  const login = useCallback(
    async (password: string, email?: string) => {
      await signIn(email, password);
      setState("authenticated");
    },
    [],
  );

  const logout = useCallback(async () => {
    await signOut();
    setState("needs-login");
  }, []);

  const value = useMemo(
    () => ({ state, refresh, login, logout }),
    [state, refresh, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
