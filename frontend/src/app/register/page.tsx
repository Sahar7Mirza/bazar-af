"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Alert, Field } from "@/components/ui";
import { api, ApiError, fieldErrors } from "@/lib/api";
import { DISTRICTS } from "@/lib/types";

export default function Register() {
  const router = useRouter();
  const [role, setRole] = useState<"buyer" | "seller">("buyer");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const v = (k: string) => String(f.get(k) ?? "").trim();
    const local: Record<string, string> = {};
    if (!/^\S+@\S+\.\S+$/.test(v("email"))) local.email = "Enter a valid email address";
    if (v("password").length < 10 || !/[A-Za-z]/.test(v("password")) || !/\d/.test(v("password"))) local.password = "At least 10 characters, with letters and digits";
    if (v("full_name").length < 2) local.full_name = "Enter your name";
    if (role === "seller" && v("business_name").length < 2) local.business_name = "Enter your business name";
    setErrs(local); setErr(null);
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      await api("auth/register", { method: "POST", body: { email: v("email"), password: v("password"), full_name: v("full_name"), phone: v("phone") || null, district: v("district") || null, role, business_name: role === "seller" ? v("business_name") : null } });
      router.push("/login?registered=1");
    } catch (x) {
      setErrs(fieldErrors(x));
      setErr(x instanceof ApiError ? x.message : "Could not create the account");
    } finally { setBusy(false); }
  }
  return (
    <div className="page"><div className="narrow">
      <h1 className="center" style={{ fontSize: "2.2rem" }}>Create your account</h1>
      <form onSubmit={submit} noValidate>
        {err && <Alert kind="bad">{err}</Alert>}
        <fieldset style={{ border: 0, padding: 0, margin: "0 0 16px" }}><legend className="small" style={{ fontWeight: 500, marginBottom: 6 }}>I want to</legend>
          <div className="opt"><input type="radio" id="r-buyer" name="role" checked={role === "buyer"} onChange={() => setRole("buyer")} /><label htmlFor="r-buyer">Buy from local businesses</label></div>
          <div className="opt"><input type="radio" id="r-seller" name="role" checked={role === "seller"} onChange={() => setRole("seller")} /><label htmlFor="r-seller">Sell my products <span className="muted small">(needs admin approval)</span></label></div>
        </fieldset>
        <Field id="full_name" label="Full name" error={errs.full_name}><input id="full_name" name="full_name" autoComplete="name" aria-invalid={!!errs.full_name} /></Field>
        {role === "seller" && <Field id="business_name" label="Business name" error={errs.business_name}><input id="business_name" name="business_name" aria-invalid={!!errs.business_name} /></Field>}
        <Field id="email" label="Email" error={errs.email}><input id="email" name="email" type="email" autoComplete="email" aria-invalid={!!errs.email} /></Field>
        <Field id="password" label="Password" error={errs.password} hint="At least 10 characters, with letters and digits"><input id="password" name="password" type="password" autoComplete="new-password" aria-invalid={!!errs.password} /></Field>
        <Field id="phone" label="Phone (optional)" error={errs.phone}><input id="phone" name="phone" type="tel" autoComplete="tel" placeholder="+93 70 000 0000" /></Field>
        <Field id="district" label="District (optional)"><select id="district" name="district" defaultValue=""><option value="">Select…</option>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select></Field>
        <button className="btn lg" style={{ width: "100%" }} disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        <p className="center muted small" style={{ marginTop: 18 }}>Already registered? <Link href="/login">Sign in</Link></p>
      </form>
    </div></div>
  );
}
