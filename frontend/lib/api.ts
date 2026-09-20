const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type Company = { id: string; name: string; slug: string; currency_code: string };
export type Project = { id: string; name: string; code: string; client_name: string; location: string; status: string; progress_percent_cache: string; planned_start_date: string | null; planned_end_date: string | null; is_archived: boolean; version: number };

export function getAccessToken() { return typeof window === "undefined" ? null : sessionStorage.getItem("buildtrack_access"); }
export function setAccessToken(token: string | null) { if (typeof window !== "undefined") token ? sessionStorage.setItem("buildtrack_access", token) : sessionStorage.removeItem("buildtrack_access"); }
export function getCompanyId() { return typeof window === "undefined" ? null : localStorage.getItem("buildtrack_company"); }
export function setCompanyId(id: string | null) { if (typeof window !== "undefined") id ? localStorage.setItem("buildtrack_company", id) : localStorage.removeItem("buildtrack_company"); }

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${API_URL}/auth/refresh/`, { method: "POST", credentials: "include" });
      if (!res.ok) {
        setAccessToken(null);
        return null;
      }
      const payload = await res.json();
      if (payload?.access) setAccessToken(payload.access);
      return payload?.access ?? null;
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      setTimeout(() => { refreshInFlight = null; }, 500);
    }
  })();
  return refreshInFlight;
}

export async function api<T>(path: string, options: RequestInit = {}, companyRequired = false): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  const companyId = getCompanyId();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  // Always send X-Company-ID if we have one; strict enforcement if companyRequired
  if (companyId) headers.set("X-Company-ID", companyId);
  if (companyRequired && !companyId) {
    throw new Error("Company context required. Please select a company.");
  }
  let response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
  if (response.status === 401 && token) {
    const newAccess = await refreshAccess();
    if (newAccess) {
      headers.set("Authorization", `Bearer ${newAccess}`);
      response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
    } else {
      // Refresh failed -> clear and redirect to login
      if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("buildtrack:auth-expired"));
    }
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const msg = typeof data.detail === "string" ? data.detail : (Array.isArray(data.detail) ? data.detail.join(" ") : Object.values(data).flat().join(" ") || `Request failed (${response.status})`);
    throw new Error(msg);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
