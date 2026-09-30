"use client";
import Link from "next/link";
import { SellerShell } from "@/components/SellerShell";
import { ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { afn } from "@/lib/format";
import type { Order, Page, Product } from "@/lib/types";

export default function SellerHome() {
  const orders = useLoad(() => api<Page<Order>>("orders", { query: { page_size: 100 } }), []);
  const prods = useLoad(() => api<Page<Product>>("sellers/me/products", { query: { page_size: 100 } }), []);
  const o = orders.data?.items ?? [], p = prods.data?.items ?? [];
  const count = (s: string) => o.filter((x) => x.status === s).length;
  const revenue = o.filter((x) => x.status === "completed").reduce((s, x) => s + Number(x.total_afn), 0);
  const top = new Map<string, number>();
  for (const x of o) if (x.status !== "cancelled") for (const i of x.items) top.set(i.product_name, (top.get(i.product_name) ?? 0) + i.quantity);
  const best = [...top.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  return (
    <SellerShell title="My shop">
      {orders.loading || prods.loading ? <LoadingRows n={3} /> : orders.error || prods.error ? <ErrorState error={orders.error ?? prods.error} retry={() => { orders.reload(); prods.reload(); }} /> : (<>
        <div className="grid g4">
          {[["To confirm", count("pending")], ["In progress", count("confirmed") + count("ready")], ["Completed", count("completed")], ["Low stock", p.filter((x) => x.stock_qty < 10).length]].map(([l, n]) => <div className="card" key={l as string}><div className="stat">{n}</div><div className="stat-l">{l}</div></div>)}
        </div>
        <div className="grid g2" style={{ marginTop: 24 }}>
          <div className="card"><h3>Completed sales</h3><div className="stat">{afn(revenue)}</div><p className="muted small">Recorded value of completed orders (payments settled outside the platform).</p></div>
          <div className="card"><h3>Top products</h3>{best.length ? <ol style={{ paddingLeft: 20, margin: 0 }}>{best.map(([n, q]) => <li key={n}>{n} <span className="muted">— {q} sold</span></li>)}</ol> : <p className="muted">No orders yet.</p>}</div>
        </div>
        <div className="row" style={{ marginTop: 24 }}><Link className="btn" href="/seller/products/new">Add product</Link><Link className="btn quiet" href="/seller/orders">View orders</Link></div>
      </>)}
    </SellerShell>
  );
}
