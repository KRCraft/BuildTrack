const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type Company = { id: string; name: string; slug: string; currency_code: string };
export type Project = { id: string; name: string; code: string; client_name: string; location: string; status: string; progress_percent_cache: string; planned_start_date: string | null; planned_end_date: string | null; is_archived: boolean; version: number };

export function getAccessToken() { return typeof window === "undefined" ? null : sessionStorage.getItem("buildtrack_access"); }
export function setAccessToken(token: string | null) { if (typeof window !== "undefined") token ? sessionStorage.setItem("buildtrack_access", token) : sessionStorage.removeItem("buildtrack_access"); }
export function getCompanyId() { return typeof window === "undefined" ? null : localStorage.getItem("buildtrack_company"); }
export function setCompanyId(id: string | null) { if (typeof window !== "undefined") id ? localStorage.setItem("buildtrack_company", id) : localStorage.removeItem("buildtrack_company"); }

export async function api<T>(path: string, options: RequestInit = {}, companyRequired = false): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  const companyId = getCompanyId();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (companyRequired && companyId) headers.set("X-Company-ID", companyId);
  let response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
  if (response.status === 401 && token) {
    const refreshed = await fetch(`${API_URL}/auth/refresh/`, { method: "POST", credentials: "include" });
    if (refreshed.ok) {
      const payload = await refreshed.json(); setAccessToken(payload.access); headers.set("Authorization", `Bearer ${payload.access}`);
      response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
    }
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : Object.values(data).flat().join(" ") || "Something went wrong.");
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
