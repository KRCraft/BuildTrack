"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { api, setAccessToken } from "@/lib/api";
import { Button, Input, Alert, Label } from "@/components/ui";
import { useAuth } from "@/components/auth-provider";

export default function LoginPage() {
  const router = useRouter(); const { refresh } = useAuth(); const [error, setError] = useState(""); const [pending, setPending] = useState(false); const [show, setShow] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(""); setPending(true); const data = new FormData(event.currentTarget); try { const result = await api<{access:string}>("/auth/login/", {method:"POST", body: JSON.stringify({email:data.get("email"), password:data.get("password")})}); setAccessToken(result.access); await refresh(); router.push("/dashboard"); } catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in."); } finally { setPending(false); } }
  return <main className="grid min-h-screen place-items-center bg-[#f6f5f0] p-4 sm:p-6"><form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-[#e5e8e3] bg-white p-6 sm:p-8 shadow-panel animate-fadeIn"><div className="mb-8"><div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-moss font-bold text-white">B</div><h1 className="text-2xl font-bold tracking-tight">Welcome back</h1><p className="mt-2 text-sm text-[#65716a]">Sign in to manage your company’s work — works on any device.</p></div>{error && <Alert variant="error" className="mb-4">{error}</Alert>}<Label className="mb-4">Email<Input className="mt-1.5" type="email" name="email" required placeholder="you@company.com" autoComplete="email" autoFocus /></Label><Label className="mb-6">Password<div className="relative mt-1.5"><Input type={show ? "text" : "password"} name="password" required placeholder="Your password (min 10 chars)" autoComplete="current-password" className="pr-10" /><button type="button" aria-label={show ? "Hide password" : "Show password"} onClick={() => setShow(!show)} className="absolute inset-y-0 right-0 grid w-10 place-items-center text-[#8a948e] hover:text-ink">{show ? <EyeOff size={16}/> : <Eye size={16}/>}</button></div></Label><Button className="w-full" size="lg" loading={pending}>{pending ? "Signing in…" : "Sign in"}</Button><p className="mt-6 text-center text-sm text-[#65716a]">New to BuildTrack? <Link className="font-semibold text-moss hover:underline" href="/register">Create your account</Link> · <Link className="text-[#65716a] hover:text-ink" href="/register">Forgot password?</Link></p></form></main>;
}
