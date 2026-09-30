"use client";
import Link from "next/link";
import { useState } from "react";
import { SellerShell } from "@/components/SellerShell";
import { Alert, EmptyState, ErrorState, LoadingRows, Pager, StatusChip, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { afn } from "@/lib/format";
import type { Page, Product } from "@/lib/types";

export default function SellerProducts() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const res = useLoad(() => api<Page<Product>>("sellers/me/products", { query: { page, q, page_size: 10 } }), [page, q]);
  async function toggle(p: Product) { setErr(null); try { await api(`products/${p.id}`, { method: "PATCH", body: { status: p.status === "active" ? "hidden" : "active" } }); res.reload(); } catch (x) { setErr(x instanceof ApiError ? x.message : "Failed"); } }
  async function del(p: Product) { if (!window.confirm(`Delete “${p.name}”? Past orders keep their record.`)) return; try { await api(`products/${p.id}`, { method: "DELETE" }); res.reload(); } catch (x) { setErr(x instanceof ApiError ? x.message : "Failed"); } }
  return (
    <SellerShell title="Products">
      <div className="row between" style={{ marginBottom: 16 }}>
        <div><label className="sr" htmlFor="pq">Search your products</label><input id="pq" type="search" placeholder="Search…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></div>
        <Link className="btn" href="/seller/products/new">Add product</Link>
      </div>
      {err && <Alert kind="bad">{err}</Alert>}
      {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? (
        <EmptyState emoji="🧺" title="No products yet" text="Add your first product to start selling." action={<Link className="btn" href="/seller/products/new">Add product</Link>} />
      ) : (<>
        <div className="table-wrap"><table>
          <thead><tr><th>Name</th><th className="num">Price</th><th className="num">Stock</th><th>Status</th><th><span className="sr">Actions</span></th></tr></thead>
          <tbody>{res.data.items.map((p) => (
            <tr key={p.id}><td>{p.name}</td><td className="num">{afn(p.price_afn)}</td><td className="num">{p.stock_qty}</td>
              <td><StatusChip status={p.hidden_by_admin ? "hidden by admin" : p.status} /></td>
              <td><div className="row" style={{ justifyContent: "flex-end" }}><Link className="btn quiet sm" href={`/seller/products/${p.id}`}>Edit</Link>
                <button className="btn quiet sm" disabled={p.hidden_by_admin} onClick={() => toggle(p)}>{p.status === "active" ? "Hide" : "Show"}</button>
                <button className="btn quiet sm" style={{ color: "var(--bad)" }} onClick={() => del(p)}>Delete</button></div></td></tr>))}</tbody>
        </table></div>
        <Pager page={res.data} onPage={setPage} />
      </>)}
    </SellerShell>
  );
}
