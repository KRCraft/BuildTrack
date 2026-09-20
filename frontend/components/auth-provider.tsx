"use client";
import { createContext, ReactNode, useContext, useEffect, useState, useCallback } from "react";
import { api, Company, getAccessToken, setAccessToken, setCompanyId } from "@/lib/api";

type User = { id: string; email: string; first_name: string; last_name: string };
type AuthValue = { user: User | null; companies: Company[]; loading: boolean; refresh: () => Promise<void>; signOut: () => Promise<void> };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null), [companies, setCompanies] = useState<Company[]>([]), [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try {
      // Try to hydrate access token from HttpOnly refresh cookie if no access token
      if (!getAccessToken()) {
        const result = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/auth/refresh/`, { method: "POST", credentials: "include" });
        if (result.ok) {
          const data = await result.json();
          if (data?.access) setAccessToken(data.access);
        }
      }
      // If still no token, we are unauthenticated
      if (!getAccessToken()) {
        setUser(null); setCompanies([]); return;
      }
      const [me, organisations] = await Promise.all([api<User>("/auth/me/"), api<Company[]>("/companies/")]);
      setUser(me); setCompanies(organisations);
      if (organisations.length && !localStorage.getItem("buildtrack_company")) setCompanyId(organisations[0].id);
    } catch {
      setUser(null); setCompanies([]);
    } finally {
      setLoading(false);
    }
  }, []);
  const signOut = async () => {
    try { await api<void>("/auth/logout/", { method: "POST" }); } catch {}
    finally { setAccessToken(null); setCompanyId(null); setUser(null); setCompanies([]); }
  };
  useEffect(() => {
    refresh();
    const onAuthExpired = () => { setAccessToken(null); setUser(null); setCompanies([]); };
    window.addEventListener("buildtrack:auth-expired", onAuthExpired);
    // Cross-tab sync for company switch
    const onStorage = (e: StorageEvent) => { if (e.key === "buildtrack_company") refresh(); };
    window.addEventListener("storage", onStorage);
    return () => { window.removeEventListener("buildtrack:auth-expired", onAuthExpired); window.removeEventListener("storage", onStorage); };
  }, [refresh]);
  return <AuthContext.Provider value={{ user, companies, loading, refresh, signOut }}>{children}</AuthContext.Provider>;
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("AuthProvider missing"); return context; }
