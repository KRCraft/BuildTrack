"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, Building2, FolderKanban, LogOut, Package, ReceiptText, Settings, Truck, Users } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { getCompanyId, setCompanyId } from "@/lib/api";

const nav = [{ href: "/dashboard", label: "Overview", icon: BarChart3 }, { href: "/projects", label: "Projects", icon: FolderKanban }, { href: "/materials", label: "Materials", icon: Package }, { href: "/inventory", label: "Inventory", icon: Truck }, { href: "/expenses", label: "Expenses", icon: ReceiptText }, { href: "/suppliers", label: "Suppliers", icon: Truck }, { href: "/team", label: "Team", icon: Users }, { href: "/settings", label: "Settings", icon: Settings }];
export function Shell({ children }: { children: React.ReactNode }) {
  const { user, companies, signOut } = useAuth(); const path = usePathname(); const router = useRouter();
  return <div className="min-h-screen md:grid md:grid-cols-[252px_1fr]">
    <aside className="hidden min-h-screen border-r border-[#e5e8e3] bg-white p-5 md:block"><Link href="/dashboard" className="mb-10 flex items-center gap-3 px-2"><span className="grid h-9 w-9 place-items-center rounded-xl bg-moss text-lg font-bold text-white">B</span><span className="text-lg font-bold tracking-tight">BuildTrack</span></Link>
      <nav className="space-y-1">{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${path.startsWith(href) ? "bg-[#eaf3ee] text-moss" : "text-[#65716a] hover:bg-[#f5f7f4]"}`}><Icon size={18}/>{label}</Link>)}</nav>
      <div className="mt-10 border-t border-[#eef0ec] pt-5"><p className="px-3 text-xs font-semibold uppercase tracking-wider text-[#8a948e]">Workspace</p><select aria-label="Active company" value={getCompanyId() || ""} onChange={(e) => { setCompanyId(e.target.value); router.refresh(); window.location.reload(); }} className="mt-2 w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2 text-sm">{companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <button onClick={async () => { await signOut(); router.push("/login"); }} className="mt-8 flex items-center gap-3 px-3 text-sm font-medium text-[#65716a] hover:text-clay"><LogOut size={18}/>Sign out</button>
    </aside>
    <main><header className="flex h-16 items-center justify-between border-b border-[#e5e8e3] bg-white px-5 md:px-8"><div className="flex items-center gap-2 font-bold md:hidden"><Building2 size={19} className="text-moss"/> BuildTrack</div><div className="ml-auto text-right"><p className="text-sm font-semibold">{user ? `${user.first_name} ${user.last_name}` : ""}</p><p className="text-xs text-[#78847d]">{user?.email}</p></div></header><div className="mx-auto max-w-7xl p-5 md:p-8">{children}</div></main>
  </div>;
}
