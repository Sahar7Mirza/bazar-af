"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Alert, EmptyState, Field } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

function Form() {
  const token = useSearchParams().get("token") ?? "";
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [fieldErr, setFieldErr] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  if (!token) return <EmptyState icon="lock" title="This link is incomplete" text="Open the link from your email again, or ask for a new one." action={<Link className="btn" href="/forgot-password">Request a new link</Link>} />;
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const pw = String(f.get("password") ?? ""), again = String(f.get("again") ?? "");
    setErr(null); setFieldErr(undefined);
    if (pw.length < 10 || !/[A-Za-z]/.test(pw) || !/\d/.test(pw)) { setFieldErr("At least 10 characters, with letters and digits"); return; }
    if (pw !== again) { setFieldErr("The two passwords do not match"); return; }
    setBusy(true);
    try { await api("auth/reset-password", { method: "POST", body: { token, password: pw } }); setDone(true); }
    catch (x) { setErr(x instanceof ApiError && x.code === "invalid_token" ? "This link is invalid or has expired. Please request a new one." : "Could not change the password. Try again."); }
    finally { setBusy(false); }
  }
  if (done) return <><Alert kind="ok"><strong>Password changed.</strong> You were signed out everywhere for safety.</Alert><p className="center"><Link className="btn" href="/login">Sign in</Link></p></>;
  return (
    <form onSubmit={submit} noValidate>
      {err && <Alert kind="bad">{err} <Link href="/forgot-password">Request a new link</Link></Alert>}
      <Field id="password" label="New password" error={fieldErr} hint="At least 10 characters, with letters and digits"><input id="password" name="password" type="password" autoComplete="new-password" required /></Field>
      <Field id="again" label="Type it again"><input id="again" name="again" type="password" autoComplete="new-password" required /></Field>
      <button className="btn lg" style={{ width: "100%" }} disabled={busy}>{busy ? "Saving…" : "Change password"}</button>
    </form>
  );
}
export default function Reset() {
  return <div className="page"><div className="narrow"><h1 className="center" style={{ fontSize: "2.2rem" }}>Choose a new password</h1><Suspense><Form /></Suspense></div></div>;
}
