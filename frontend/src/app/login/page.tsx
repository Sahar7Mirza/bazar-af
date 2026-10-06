"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Alert, Field } from "@/components/ui";
import { useSession } from "@/components/Session";
import type { User } from "@/lib/types";

function Form() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");
  const { setUser } = useSession();
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true); setErr(null);
    const f = new FormData(e.currentTarget);
    try {
      const res = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: f.get("email"), password: f.get("password") }) });
      const data = await res.json();
      if (!res.ok) { setErr(data?.error?.message ?? "Sign in failed"); return; }
      const user = data.user as User;
      setUser(user);
      router.push(next && next.startsWith("/") ? next : user.role === "admin" ? "/admin" : user.role === "seller" ? "/seller" : "/products");
    } catch { setErr("Cannot reach the server. Try again."); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} noValidate>
      {params.get("registered") && <Alert kind="ok">Account created. We emailed you a link to confirm your address. You can sign in now.</Alert>}
      {err && <Alert kind="bad">{err}</Alert>}
      <Field id="email" label="Email"><input id="email" name="email" type="email" autoComplete="email" required /></Field>
      <Field id="password" label="Password"><input id="password" name="password" type="password" autoComplete="current-password" required /></Field>
      <p className="small" style={{ textAlign: "right", marginTop: -8 }}><Link href="/forgot-password">Forgot password?</Link></p>
      <button className="btn lg" style={{ width: "100%" }} disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      <p className="center muted small" style={{ marginTop: 18 }}>New here? <Link href="/register">Create an account</Link></p>
    </form>
  );
}
export default function Login() {
  return <div className="page"><div className="narrow"><h1 className="center" style={{ fontSize: "2.2rem" }}>Sign in</h1><Suspense><Form /></Suspense></div></div>;
}
