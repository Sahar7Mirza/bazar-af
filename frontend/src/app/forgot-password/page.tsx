"use client";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { Alert, Field } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

export default function Forgot() {
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true); setErr(null);
    const email = String(new FormData(e.currentTarget).get("email") ?? "").trim();
    try { await api("auth/forgot-password", { method: "POST", body: { email } }); setSent(true); }
    catch (x) { setErr(x instanceof ApiError && x.status === 422 ? "Enter a valid email address" : "Something went wrong. Try again."); }
    finally { setBusy(false); }
  }
  return (
    <div className="page"><div className="narrow">
      <h1 className="center" style={{ fontSize: "2.2rem" }}>Forgot your password?</h1>
      {sent ? (
        <Alert kind="ok"><strong>Check your inbox.</strong> If an account exists for that email, we sent a link to choose a new password. It works for 60 minutes. Look in spam if you do not see it.</Alert>
      ) : (
        <form onSubmit={submit} noValidate>
          <p className="muted center">Enter your email and we will send you a link to choose a new password.</p>
          {err && <Alert kind="bad">{err}</Alert>}
          <Field id="email" label="Email"><input id="email" name="email" type="email" autoComplete="email" required /></Field>
          <button className="btn lg" style={{ width: "100%" }} disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button>
        </form>
      )}
      <p className="center muted small" style={{ marginTop: 18 }}><Link href="/login">Back to sign in</Link></p>
    </div></div>
  );
}
