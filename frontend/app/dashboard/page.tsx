"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, FolderKanban, FolderOpen, CheckCircle2, Archive } from "lucide-react";
import { Shell } from "@/components/shell";
import { api, Project } from "@/lib/api";
import { Card, Badge, Skeleton, Alert, EmptyState, PageHeader, Button } from "@/components/ui";
import { useAuth } from "@/components/auth-provider";

type Dashboard = { company: {name:string}; total_projects:number; active_projects:number; completed_projects:number; archived_projects:number; recent_projects:Project[]; recent_audit_actions:{id:string;action:string;created_at:string;actor_snapshot:{name?:string}}[] };
export default function DashboardPage() {
  const { loading, companies } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { if (!loading && companies.length) api<Dashboard>("/dashboard/company/", {}, true).then(setData).catch(e=>setError(e.message)); }, [loading, companies.length]);
  if (loading) return <div className="p-6 md:p-8 space-y-4"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[1,2,3,4].map(i=><Skeleton key={i} className="h-28" />)}</div><Skeleton className="h-64" /></div>;
  if (!companies.length) return <Shell><Welcome /></Shell>;
  if (error) return <Shell><Alert variant="error">{error}</Alert></Shell>;
  const metrics=[{label:"All projects",value:data?.total_projects||0,icon:FolderKanban},{label:"Active",value:data?.active_projects||0,icon:FolderOpen},{label:"Completed",value:data?.completed_projects||0,icon:CheckCircle2},{label:"Archived",value:data?.archived_projects||0,icon:Archive}];
  const recentProjects=data?.recent_projects ?? [];
  const recentActions=data?.recent_audit_actions ?? [];
  return <Shell>
    <PageHeader eyebrow={data?.company.name} title="Good operational visibility." description="Your company’s project activity at a glance. Flexibly adapts to any screen." action={<Link href="/projects/new"><Button size="lg">New project</Button></Link>} />
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{metrics.map(({label,value,icon:Icon})=><Card key={label} className="p-5" hover><Icon size={20} className="text-moss"/><p className="mt-5 text-3xl font-bold tabular-nums">{value}</p><p className="mt-1 text-sm text-[#65716a]">{label}</p></Card>)}</div>
    <div className="mt-7 grid gap-7 lg:grid-cols-[1.5fr_1fr]">
      <Card>
        <div className="flex items-center justify-between border-b border-[#edf0eb] p-5"><h2 className="font-bold">Recently updated</h2><Link href="/projects" className="inline-flex items-center gap-1 text-sm font-semibold text-moss hover:underline">All projects <ArrowUpRight size={14}/></Link></div>
        <div className="divide-y divide-[#f0f2ee]">
          {recentProjects.length===0 ? <EmptyState title="No projects yet" description="Create your first project to see it here." action={<Link href="/projects/new"><Button>New project</Button></Link>} /> : recentProjects.map(p=>(
            <Link key={p.id} href={`/projects/${p.id}`} className="flex items-center justify-between p-4 hover:bg-[#fafbf9] transition">
              <div className="min-w-0"><p className="truncate font-medium">{p.name}</p><p className="text-xs text-[#78847d]">{p.code} · {p.client_name}</p></div>
              <Badge value={p.status} />
            </Link>
          ))}
        </div>
      </Card>
      <Card>
        <div className="border-b border-[#edf0eb] p-5"><h2 className="font-bold">Recent activity</h2></div>
        <div className="divide-y divide-[#f0f2ee]">
          {recentActions.length===0 ? <EmptyState title="No activity" description="Actions will appear here." /> : recentActions.map(a=>(
            <div key={a.id} className="p-4"><p className="text-sm font-medium">{a.action.replace(/\./g," · ")}</p><p className="text-xs text-[#78847d]">{new Date(a.created_at).toLocaleString()} {a.actor_snapshot?.name ? `· ${a.actor_snapshot.name}` : ""}</p></div>
          ))}
        </div>
      </Card>
    </div>
  </Shell>;
}
function Welcome() { return <div className="mx-auto max-w-xl py-20 text-center"><p className="text-sm font-semibold text-moss">Welcome to BuildTrack</p><h1 className="mt-2 text-4xl font-bold tracking-tight">Set up your company workspace.</h1><p className="mt-3 text-[#65716a]">Create a company before you start organizing construction projects and your team — responsive on mobile & desktop.</p><Link href="/settings?welcome=1" className="mt-6 inline-flex rounded-lg bg-moss px-4 py-2.5 text-sm font-semibold text-white hover:bg-moss-dark">Create company</Link></div> }
