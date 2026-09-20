"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useCallback } from "react";
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

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, companies, signOut, refresh } = useAuth();
  const path = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const handleCompanyChange = useCallback(async (value: string) => {
    setCompanyId(value);
    // No full reload - revalidate auth + soft refresh
    await refresh();
    router.refresh();
  }, [refresh, router]);

  const NavLinks = ({ onClick }: { onClick?: () => void }) => (
    <nav className="space-y-1">
      {nav.map(({ href, label, icon: Icon }) => {
        const active = path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onClick}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${active ? "bg-[#eaf3ee] text-moss" : "text-[#65716a] hover:bg-[#f5f7f4] hover:text-ink"}`}
          >
            <Icon size={18} aria-hidden />
            <span className={collapsed ? "hidden xl:inline" : ""}>{label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-[#f6f5f0]">
      {/* Desktop sidebar - flexible width */}
      <aside className={`hidden md:fixed md:inset-y-0 md:flex md:flex-col border-r border-[#e5e8e3] bg-white transition-all ${collapsed ? "md:w-[72px]" : "md:w-[252px]"}`}>
        <div className={`flex items-center gap-3 px-5 py-5 ${collapsed ? "justify-center" : ""}`}>
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-moss text-lg font-bold text-white shrink-0">B</span>
            {!collapsed && <span className="text-lg font-bold tracking-tight">BuildTrack</span>}
          </Link>
          <button aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={() => setCollapsed(!collapsed)} className="ml-auto hidden xl:grid h-7 w-7 place-items-center rounded-md text-[#8a948e] hover:bg-[#f5f7f4]">{collapsed ? "»" : "«"}</button>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-2"><NavLinks /></div>
        <div className="border-t border-[#eef0ec] p-4">
          {!collapsed && <p className="px-2 text-xs font-semibold uppercase tracking-wider text-[#8a948e]">Workspace</p>}
          <select
            aria-label="Active company"
            value={getCompanyId() || ""}
            onChange={(e) => handleCompanyChange(e.target.value)}
            className="mt-2 w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2 text-sm focus:border-moss focus:ring-2 focus:ring-moss/15"
          >
            {companies.length === 0 && <option value="">No company</option>}
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button onClick={async () => { await signOut(); router.push("/login"); }} className="mt-4 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-[#65716a] hover:bg-[#f5f7f4] hover:text-clay">
            <LogOut size={18} /> {!collapsed && "Sign out"}
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setMobileOpen(false)} aria-hidden />
          <aside className="absolute inset-y-0 left-0 w-[280px] bg-white shadow-xl animate-fadeIn">
            <div className="flex items-center justify-between border-b border-[#e5e8e3] px-5 py-4">
              <span className="flex items-center gap-2 font-bold"><Building2 size={19} className="text-moss" /> BuildTrack</span>
              <button aria-label="Close menu" onClick={() => setMobileOpen(false)} className="grid h-8 w-8 place-items-center rounded-lg hover:bg-[#f5f7f4]"><X size={18} /></button>
            </div>
            <div className="p-4"><NavLinks onClick={() => setMobileOpen(false)} /></div>
          </aside>
        </div>
      )}

      {/* Main */}
      <div className={`transition-all ${collapsed ? "md:pl-[72px]" : "md:pl-[252px]"}`}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[#e5e8e3] bg-white/80 px-4 backdrop-blur-md md:px-8">
          <button aria-label="Open navigation" onClick={() => setMobileOpen(true)} className="grid h-9 w-9 place-items-center rounded-lg border border-[#e5e8e3] md:hidden"><Menu size={18} /></button>
          <div className="hidden items-center gap-2 font-bold md:flex"><Building2 size={19} className="text-moss md:hidden" /> <span className="md:hidden">BuildTrack</span></div>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold leading-none">{user ? `${user.first_name} ${user.last_name}`.trim() || user.email : ""}</p>
              <p className="text-xs text-[#78847d]">{user?.email}</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-[#eaf3ee] grid place-items-center text-sm font-bold text-moss">{user?.first_name?.[0] || user?.email?.[0] || "?"}</div>
          </div>
        </header>
        <div className="mx-auto max-w-7xl p-4 md:p-8">{children}</div>
      </div>
    </div>
  );
}
