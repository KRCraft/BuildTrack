"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { Shell } from "@/components/shell";
import { api, Project } from "@/lib/api";
import { Badge, Card, Input, Select, PageHeader, Button, Skeleton, EmptyState, Alert } from "@/components/ui";
import { useAuth } from "@/components/auth-provider";

export default function ProjectsPage() {
  const { loading, companies } = useAuth();
  const [projects,setProjects]=useState<Project[]>([]);
  const [search,setSearch]=useState("");
  const [status,setStatus]=useState("");
  const [error,setError]=useState("");
  const [isLoading, setIsLoading] = useState(false);
  useEffect(()=>{ if(!loading && companies.length) {
    setIsLoading(true);
    const query=new URLSearchParams();
    if(search) query.set("search",search);
    if(status) query.set("status",status);
    // Handle both paginated {results:[]} and bare array
    api<any>(`/projects/?${query}`,{},true).then(res=>{
      const list = Array.isArray(res) ? res : (res.results || res);
      setProjects(Array.isArray(list) ? list : []);
    }).catch(e=>setError(e.message)).finally(()=>setIsLoading(false));
  }},[loading,companies.length,search,status]);

  return <Shell>
    <PageHeader eyebrow="Delivery" title="Projects" description="Keep every active build visible and accountable — card view on mobile, table on desktop." action={<Link href="/projects/new"><Button>New project</Button></Link>} />
    <Card>
      <div className="flex flex-col gap-3 border-b border-[#edf0eb] p-4 sm:flex-row">
        <div className="relative flex-1"><Search className="absolute left-3 top-3 text-[#87928b]" size={17} aria-hidden/><Input value={search} onChange={e=>setSearch(e.target.value)} className="pl-9" placeholder="Search by project, code, or client" aria-label="Search projects" /></div>
        <Select value={status} onChange={e=>setStatus(e.target.value)} className="sm:w-48" aria-label="Filter by status"><option value="">All statuses</option><option value="DRAFT">Draft</option><option value="ACTIVE">Active</option><option value="ON_HOLD">On hold</option><option value="COMPLETED">Completed</option><option value="ARCHIVED">Archived</option></Select>
      </div>
      {error ? <div className="p-4"><Alert variant="error">{error}</Alert></div> : isLoading ? <div className="p-4 space-y-3">{[1,2,3].map(i=><Skeleton key={i} className="h-16" />)}</div> : (
        <>
          {/* Mobile cards */}
          <div className="grid gap-3 p-4 sm:hidden">
            {projects.length===0 ? <EmptyState title="No projects" description="Try adjusting filters or create a new project." /> : projects.map(p=>(
              <Link key={p.id} href={`/projects/${p.id}`} className="rounded-xl border border-[#e5e8e3] p-4 hover:bg-[#fafbf9] transition">
                <div className="flex items-start justify-between gap-2"><p className="font-semibold line-clamp-1">{p.name}</p><Badge value={p.status} /></div>
                <p className="mt-1 text-sm text-[#65716a]">{p.code} · {p.client_name}</p>
                <p className="mt-1 text-xs text-[#78847d]">{p.location || "No location"}</p>
              </Link>
            ))}
          </div>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]"><tr><th className="px-5 py-3 font-semibold">Project</th><th className="px-5 py-3 font-semibold">Client</th><th className="px-5 py-3 font-semibold">Status</th><th className="px-5 py-3 font-semibold">Progress</th></tr></thead>
              <tbody className="divide-y divide-[#f0f2ee]">
                {projects.length===0 ? <tr><td colSpan={4} className="p-8 text-center text-[#65716a]">No projects match your filters.</td></tr> : projects.map(p=>(
                  <tr key={p.id} className="hover:bg-[#fafbf9] transition"><td className="px-5 py-4"><Link href={`/projects/${p.id}`} className="font-medium hover:text-moss hover:underline">{p.name}</Link><p className="text-xs text-[#78847d]">{p.code}</p></td><td className="px-5 py-4 text-[#65716a]">{p.client_name}</td><td className="px-5 py-4"><Badge value={p.status} /></td><td className="px-5 py-4 tabular-nums">{p.progress_percent_cache}%</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  </Shell>;
}
