import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as api from "./api";
import type { AuthUser } from "./api";

const STORAGE_KEY = "campus-customs-auth";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fields: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      setReady(true);
      return;
    }
    const storedToken: string = JSON.parse(stored).token;
    api
      .fetchMe(storedToken)
      .then((me) => {
        setToken(storedToken);
        setUser(me);
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
      })
      .finally(() => setReady(true));
  }, []);

  const persist = (newToken: string, newUser: AuthUser) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: newToken }));
    setToken(newToken);
    setUser(newUser);
  };

  const login: AuthContextValue["login"] = async (email, password) => {
    const res = await api.login({ email, password });
    persist(res.token, res.user);
  };

  const signup: AuthContextValue["signup"] = async (fields) => {
    const res = await api.signup(fields);
    persist(res.token, res.user);
  };

  const logout = () => {
    if (token) api.logout(token).catch(() => {});
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, ready, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
