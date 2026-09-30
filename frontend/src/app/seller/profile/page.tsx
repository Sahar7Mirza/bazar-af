"use client";
import { useState, type FormEvent } from "react";
import { SellerShell } from "@/components/SellerShell";
import { Alert, ErrorState, Field, LoadingRows, useLoad } from "@/components/ui";
import { api, ApiError, fieldErrors } from "@/lib/api";
import { DISTRICTS, type Category, type Seller } from "@/lib/types";

export default function ShopProfile() {
  const me = useLoad(() => api<Seller>("sellers/me"), []);
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ kind: "ok" | "bad"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget), v = (k: string) => String(f.get(k) ?? "").trim() || null;
    setBusy(true); setMsg(null); setErrs({});
    try { await api("sellers/me", { method: "PUT", body: { business_name: v("business_name"), category_id: v("category_id") ? Number(v("category_id")) : null, description: v("description"), district: v("district"), address_note: v("address_note"), phone: v("phone"), opening_hours: v("opening_hours") } }); setMsg({ kind: "ok", text: "Saved." }); me.reload(); }
    catch (x) { setErrs(fieldErrors(x)); setMsg({ kind: "bad", text: x instanceof ApiError ? x.message : "Could not save" }); } finally { setBusy(false); }
  }
  const d = me.data;
  return (
    <SellerShell title="Shop profile">
      {me.loading ? <LoadingRows n={4} /> : me.error || !d ? <ErrorState error={me.error} retry={me.reload} /> : (
        <form onSubmit={save} className="mid" style={{ padding: 0 }} noValidate>
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          <Field id="business_name" label="Business name" error={errs.business_name}><input id="business_name" name="business_name" defaultValue={d.business_name} /></Field>
          <Field id="description" label="About your business"><textarea id="description" name="description" defaultValue={d.description ?? ""} /></Field>
          <div className="grid g2">
            <Field id="category_id" label="Main category"><select id="category_id" name="category_id" defaultValue={d.category_id ?? ""}><option value="">Select…</option>{(cats.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
            <Field id="district" label="District" error={errs.district}><select id="district" name="district" defaultValue={d.district ?? ""}><option value="">Select…</option>{DISTRICTS.map((x) => <option key={x}>{x}</option>)}</select></Field>
            <Field id="phone" label="Phone"><input id="phone" name="phone" defaultValue={d.phone ?? ""} /></Field>
            <Field id="opening_hours" label="Opening hours"><input id="opening_hours" name="opening_hours" defaultValue={d.opening_hours ?? ""} /></Field>
          </div>
          <Field id="address_note" label="Address / landmark"><input id="address_note" name="address_note" defaultValue={d.address_note ?? ""} /></Field>
          <button className="btn" disabled={busy}>{busy ? "Saving…" : "Save changes"}</button>
        </form>
      )}
    </SellerShell>
  );
}
