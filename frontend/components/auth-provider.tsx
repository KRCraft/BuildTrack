"use client";
import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { api, Company, getAccessToken, setAccessToken, setCompanyId } from "@/lib/api";

type User = { id: string; email: string; first_name: string; last_name: string };
type AuthValue = { user: User | null; companies: Company[]; loading: boolean; refresh: () => Promise<void>; signOut: () => Promise<void> };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null), [companies, setCompanies] = useState<Company[]>([]), [loading, setLoading] = useState(true);
  const refresh = async () => {
    try {
      if (!getAccessToken()) { const result = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/auth/refresh/`, { method: "POST", credentials: "include" }); if (result.ok) setAccessToken((await result.json()).access); }
      const [me, organisations] = await Promise.all([api<User>("/auth/me/"), api<Company[]>("/companies/")]);
      setUser(me); setCompanies(organisations);
      if (organisations.length && !localStorage.getItem("buildtrack_company")) setCompanyId(organisations[0].id);
    } catch { setUser(null); setCompanies([]); }
    finally { setLoading(false); }
  };
  const signOut = async () => { try { await api<void>("/auth/logout/", { method: "POST" }); } finally { setAccessToken(null); setCompanyId(null); setUser(null); setCompanies([]); } };
  useEffect(() => { refresh(); }, []);
  return <AuthContext.Provider value={{ user, companies, loading, refresh, signOut }}>{children}</AuthContext.Provider>;
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("AuthProvider missing"); return context; }
