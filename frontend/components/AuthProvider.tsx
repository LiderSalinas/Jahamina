"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

const TOKEN_KEY = "jahamina_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const loadUser = useCallback(
    async (currentToken: string) => {
      try {
        setUser(await api.me(currentToken));
        setToken(currentToken);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) clearSession();
        else throw error;
      }
    },
    [clearSession],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }
      loadUser(storedToken)
        .catch(() => clearSession())
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [clearSession, loadUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login(email, password);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      await loadUser(response.access_token);
    },
    [loadUser],
  );

  const logout = useCallback(() => {
    clearSession();
    router.push("/login");
  }, [clearSession, router]);

  const refreshUser = useCallback(async () => {
    if (token) await loadUser(token);
  }, [loadUser, token]);

  const value = useMemo(
    () => ({ user, token, loading, login, logout, refreshUser }),
    [user, token, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return context;
}
