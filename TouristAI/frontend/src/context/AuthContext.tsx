import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import * as authApi from "../api/auth";
import { getAccessToken, setAccessToken } from "../api/session";

export type AuthUser = { user_id: string; email: string; display_name: string };
type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  profileComplete: boolean;
  markProfileComplete: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileComplete, setProfileComplete] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!getAccessToken()) return;
      try {
        const current = await authApi.currentUser();
        if (active) {
          setUser(current);
          setProfileComplete(true);
        }
      } catch {
        setAccessToken(null);
      }
    })().finally(() => active && setLoading(false));
    if (!getAccessToken()) setLoading(false);
    return () => { active = false; };
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    profileComplete,
    markProfileComplete: () => setProfileComplete(true),
    login: async (email, password) => { const data = await authApi.login(email, password); setUser(data.user); setProfileComplete(true); },
    register: async (email, password, displayName) => { const data = await authApi.register(email, password, displayName); setUser(data.user); setProfileComplete(false); },
    logout: async () => {
      try {
        await authApi.logout();
      } finally {
        setUser(null);
        setProfileComplete(false);
      }
    }
  }), [user, loading, profileComplete]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
};
