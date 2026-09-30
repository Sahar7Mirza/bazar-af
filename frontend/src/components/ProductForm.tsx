"use client";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Alert, Field, useLoad } from "@/components/ui";
import { api, ApiError, fieldErrors } from "@/lib/api";
import type { Category, Product } from "@/lib/types";

export function ProductForm({ product }: { product?: Product }) {
  const router = useRouter();
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget), v = (k: string) => String(f.get(k) ?? "").trim();
    const local: Record<string, string> = {};
    if (v("name").length < 2) local.name = "Enter a product name";
    if (v("price_afn") === "" || Number(v("price_afn")) < 0 || Number.isNaN(Number(v("price_afn")))) local.price_afn = "Enter a price of 0 or more";
    if (!Number.isInteger(Number(v("stock_qty"))) || Number(v("stock_qty")) < 0) local.stock_qty = "Enter a whole number, 0 or more";
    setErrs(local); setErr(null);
    if (Object.keys(local).length) return;
    const body = { name: v("name"), description: v("description") || null, category_id: v("category_id") ? Number(v("category_id")) : null, price_afn: v("price_afn"), unit: v("unit") || "piece", stock_qty: Number(v("stock_qty")), status: v("status") || "active" };
    setBusy(true);
    try { await (product ? api(`products/${product.id}`, { method: "PATCH", body }) : api("products", { method: "POST", body })); router.push("/seller/products"); }
    catch (x) { setErrs(fieldErrors(x)); setErr(x instanceof ApiError ? x.message : "Could not save"); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} noValidate className="mid" style={{ padding: 0 }}>
      {err && <Alert kind="bad">{err}</Alert>}
      <Field id="name" label="Product name" error={errs.name}><input id="name" name="name" defaultValue={product?.name} aria-invalid={!!errs.name} /></Field>
      <Field id="description" label="Description (optional)"><textarea id="description" name="description" defaultValue={product?.description ?? ""} /></Field>
      <div className="grid g2">
        <Field id="price_afn" label="Price (AFN)" error={errs.price_afn}><input id="price_afn" name="price_afn" inputMode="decimal" defaultValue={product?.price_afn} aria-invalid={!!errs.price_afn} /></Field>
        <Field id="unit" label="Unit" hint="kg, piece, box…"><input id="unit" name="unit" defaultValue={product?.unit ?? "piece"} /></Field>
        <Field id="stock_qty" label="Stock" error={errs.stock_qty}><input id="stock_qty" name="stock_qty" inputMode="numeric" defaultValue={product?.stock_qty ?? 0} aria-invalid={!!errs.stock_qty} /></Field>
        <Field id="category_id" label="Category" error={errs.category_id}><select id="category_id" name="category_id" defaultValue={product?.category_id ?? ""}><option value="">None</option>{(cats.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
      </div>
      <Field id="status" label="Visibility"><select id="status" name="status" defaultValue={product?.status ?? "active"}><option value="active">Visible in the shop</option><option value="hidden">Hidden</option></select></Field>
      <div className="row"><button className="btn" disabled={busy}>{busy ? "Saving…" : "Save product"}</button><button type="button" className="btn quiet" onClick={() => router.push("/seller/products")}>Cancel</button></div>
    </form>
  );
}
