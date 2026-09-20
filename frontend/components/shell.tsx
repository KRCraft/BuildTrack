"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useCallback, useEffect } from "react";
import { BarChart3, Building2, FolderKanban, LogOut, Menu, Package, ReceiptText, Settings, Truck, Users, X } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { getCompanyId, setCompanyId } from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Overview", icon: BarChart3 },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/materials", label: "Materials", icon: Package },
  { href: "/inventory", label: "Inventory", icon: Truck },
  { href: "/expenses", label: "Expenses", icon: ReceiptText },
  { href: "/suppliers", label: "Suppliers", icon: Truck },
  { href: "/team", label: "Team", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

const SIDEBAR_COLLAPSED_KEY = "buildtrack_sidebar_collapsed";

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, companies, signOut, refresh } = useAuth();
  const path = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Persist collapsed state via localStorage (hydrate after mount to avoid SSR mismatch)
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (stored !== null) setCollapsed(stored === "true");
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
    } catch {}
  }, [collapsed]);

  // Sync collapsed state across tabs
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === SIDEBAR_COLLAPSED_KEY && e.newValue !== null) {
        setCollapsed(e.newValue === "true");
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Keyboard shortcut Ctrl+B (and Cmd+B on macOS) to toggle sidebar
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        const target = e.target as HTMLElement | null;
        const isEditable =
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          target instanceof HTMLSelectElement ||
          (target !== null && target.isContentEditable);
        if (isEditable) return;
        e.preventDefault();
        setCollapsed((v) => !v);
      }
      if (e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen]);

  // Respect prefers-color-scheme for dark mode (Tailwind darkMode: "class")
  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      document.documentElement.classList.toggle("dark", mql.matches);
    };
    apply();
    // Modern browsers support addEventListener on MediaQueryList
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", apply);
      return () => mql.removeEventListener("change", apply);
    } else {
      // Safari fallback
      const legacy = mql as unknown as { addListener: (cb: () => void) => void; removeListener: (cb: () => void) => void };
      legacy.addListener(apply);
      return () => legacy.removeListener(apply);
    }
  }, []);

  const handleCompanyChange = useCallback(async (value: string) => {
    setCompanyId(value);
    // No full reload - revalidate auth + soft refresh
    await refresh();
    router.refresh();
  }, [refresh, router]);

  const NavLinks = ({ onClick }: { onClick?: () => void }) => (
    <nav aria-label="Primary navigation" className="space-y-1">
      {nav.map(({ href, label, icon: Icon }) => {
        const active = path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onClick}
            aria-current={active ? "page" : undefined}
            aria-label={label}
            title={collapsed ? label : undefined}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40 ${active ? "bg-[#eaf3ee] text-moss dark:bg-[#1a2e26] dark:text-[#a8d5c2]" : "text-[#65716a] hover:bg-[#f5f7f4] hover:text-ink dark:text-[#a1aea8] dark:hover:bg-[#1a2e26] dark:hover:text-[#eaf3ee]"}`}
          >
            <Icon size={18} aria-hidden="true" />
            <span className={collapsed ? "hidden xl:hidden" : ""} aria-hidden={collapsed ? true : undefined}>{label}</span>
            {collapsed && <span className="sr-only">{label}</span>}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-[#f6f5f0] dark:bg-[#0f1a15]">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-moss focus:shadow-lg">
        Skip to main content
      </a>
      {/* Desktop sidebar - flexible width */}
      <aside
        id="sidebar"
        aria-label="Sidebar"
        aria-expanded={!collapsed}
        className={`hidden md:fixed md:inset-y-0 md:flex md:flex-col border-r border-[#e5e8e3] bg-white dark:border-[#1e2e28] dark:bg-[#141f1b] transition-all ${collapsed ? "md:w-[72px]" : "md:w-[252px]"}`}
      >
        <div className={`flex items-center gap-3 px-5 py-5 ${collapsed ? "justify-center" : ""}`}>
          <Link href="/dashboard" className="flex items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40 rounded-lg">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-moss text-lg font-bold text-white shrink-0" aria-hidden="true">B</span>
            {!collapsed && <span className="text-lg font-bold tracking-tight">BuildTrack</span>}
            {collapsed && <span className="sr-only">BuildTrack home</span>}
          </Link>
          <button
            type="button"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            aria-controls="sidebar"
            title="Toggle sidebar (Ctrl+B)"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto hidden xl:grid h-7 w-7 place-items-center rounded-md text-[#8a948e] hover:bg-[#f5f7f4] dark:hover:bg-[#1e2e28] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40"
          >
            <span aria-hidden="true">{collapsed ? "»" : "«"}</span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-2"><NavLinks /></div>
        <div className="border-t border-[#eef0ec] dark:border-[#1e2e28] p-4">
          {!collapsed ? <p className="px-2 text-xs font-semibold uppercase tracking-wider text-[#8a948e]">Workspace</p> : <p className="sr-only">Workspace</p>}
          <select
            aria-label="Active company"
            value={getCompanyId() || ""}
            onChange={(e) => handleCompanyChange(e.target.value)}
            className="mt-2 w-full rounded-lg border border-[#d8ded8] dark:border-[#2a3a33] bg-white dark:bg-[#1a2e26] px-3 py-2 text-sm focus:border-moss focus:ring-2 focus:ring-moss/15 focus-visible:outline-none"
          >
            {companies.length === 0 && <option value="">No company</option>}
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={async () => { await signOut(); router.push("/login"); }}
            className="mt-4 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-[#65716a] hover:bg-[#f5f7f4] hover:text-clay dark:text-[#a1aea8] dark:hover:bg-[#1e2e28] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40"
            aria-label="Sign out"
          >
            <LogOut size={18} aria-hidden="true" /> {!collapsed ? "Sign out" : <span className="sr-only">Sign out</span>}
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setMobileOpen(false)} aria-hidden="true" />
          <aside className="absolute inset-y-0 left-0 w-[280px] bg-white dark:bg-[#141f1b] shadow-xl animate-fadeIn">
            <div className="flex items-center justify-between border-b border-[#e5e8e3] dark:border-[#1e2e28] px-5 py-4">
              <span className="flex items-center gap-2 font-bold"><Building2 size={19} className="text-moss" aria-hidden="true" /> BuildTrack</span>
              <button type="button" aria-label="Close menu" onClick={() => setMobileOpen(false)} className="grid h-8 w-8 place-items-center rounded-lg hover:bg-[#f5f7f4] dark:hover:bg-[#1e2e28] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40"><X size={18} aria-hidden="true" /></button>
            </div>
            <div className="p-4"><NavLinks onClick={() => setMobileOpen(false)} /></div>
          </aside>
        </div>
      )}

      {/* Main */}
      <div className={`transition-all ${collapsed ? "md:pl-[72px]" : "md:pl-[252px]"}`}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[#e5e8e3] dark:border-[#1e2e28] bg-white/80 dark:bg-[#141f1b]/80 px-4 backdrop-blur-md md:px-8">
          <button type="button" aria-label="Open navigation" aria-expanded={mobileOpen} aria-controls="sidebar" onClick={() => setMobileOpen(true)} className="grid h-9 w-9 place-items-center rounded-lg border border-[#e5e8e3] dark:border-[#2a3a33] md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40"><Menu size={18} aria-hidden="true" /></button>
          <div className="hidden items-center gap-2 font-bold md:flex"><Building2 size={19} className="text-moss md:hidden" aria-hidden="true" /> <span className="md:hidden">BuildTrack</span></div>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold leading-none">{user ? `${user.first_name} ${user.last_name}`.trim() || user.email : ""}</p>
              <p className="text-xs text-[#78847d] dark:text-[#a1aea8]">{user?.email}</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-[#eaf3ee] dark:bg-[#1a2e26] grid place-items-center text-sm font-bold text-moss" aria-hidden="true">{user?.first_name?.[0] || user?.email?.[0] || "?"}</div>
          </div>
        </header>
        <main id="main-content" tabIndex={-1} className="mx-auto max-w-7xl p-4 md:p-8 focus-visible:outline-none">{children}</main>
      </div>
    </div>
  );
}
