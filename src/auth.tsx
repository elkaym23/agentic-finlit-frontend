import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "./api";
import type { User } from "./types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (body: Record<string, unknown>) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
  setUser: (u: User) => void;
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) { setUser(null); return; }
    try { setUser(await api.get<User>("/api/auth/me")); } catch { setUser(null); }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    const onLogout = () => setUser(null);
    window.addEventListener("smartkids:logout", onLogout);
    return () => window.removeEventListener("smartkids:logout", onLogout);
  }, [refresh]);

  const finish = (r: { token: string; user: User }) => { setToken(r.token); setUser(r.user); return r.user; };
  const value: AuthCtx = {
    user, loading, refresh, setUser,
    login: async (email, password) => finish(await api.post("/api/auth/login", { email, password })),
    signup: async (body) => finish(await api.post("/api/auth/signup", body)),
    logout: () => { setToken(null); setUser(null); },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);
