"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setAccessToken } from "@/lib/api";
import { Button, Input } from "@/components/ui";
import { useAuth } from "@/components/auth-provider";

export default function LoginPage() {
  const router = useRouter(); const { refresh } = useAuth(); const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(""); setPending(true); const data = new FormData(event.currentTarget); try { const result = await api<{access:string}>("/auth/login/", {method:"POST", body: JSON.stringify({email:data.get("email"), password:data.get("password")})}); setAccessToken(result.access); await refresh(); router.push("/dashboard"); } catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in."); } finally { setPending(false); } }
  return <main className="grid min-h-screen place-items-center p-5"><form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-[#e5e8e3] bg-white p-8 shadow-panel"><div className="mb-8"><div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-moss font-bold text-white">B</div><h1 className="text-2xl font-bold">Welcome back</h1><p className="mt-2 text-sm text-[#65716a]">Sign in to manage your company’s work.</p></div>{error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<label className="mb-4 block text-sm font-medium">Email<Input className="mt-1.5" type="email" name="email" required placeholder="you@company.com"/></label><label className="mb-6 block text-sm font-medium">Password<Input className="mt-1.5" type="password" name="password" required placeholder="Your password"/></label><Button className="w-full" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</Button><p className="mt-6 text-center text-sm text-[#65716a]">New to BuildTrack? <Link className="font-semibold text-moss" href="/register">Create your account</Link></p></form></main>;
}
