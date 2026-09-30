"use client";
import Link from "next/link";
import { AdminShell } from "@/components/AdminShell";
import { Donut } from "@/components/charts";
import { ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { afn } from "@/lib/format";

interface Stats { users: Record<string, number>; sellers_pending: number; sellers_approved: number; products_active: number; orders: Record<string, number>; orders_total: number; payment_preference: Record<string, number>; mobile_money_providers: Record<string, number>; total_value_afn: string }

export default function AdminHome() {
  const s = useLoad(() => api<Stats>("admin/stats"), []);
  const d = s.data;
  return (
    <AdminShell title="Administration">
      {s.loading ? <LoadingRows n={4} /> : s.error || !d ? <ErrorState error={s.error} retry={s.reload} /> : (<>
        <div className="grid g4">
          {[["Users", Object.values(d.users).reduce((a, b) => a + b, 0)], ["Approved sellers", d.sellers_approved], ["Products", d.products_active], ["Orders", d.orders_total]].map(([l, n]) => <div className="card" key={l as string}><div className="stat">{n}</div><div className="stat-l">{l}</div></div>)}
        </div>
        {d.sellers_pending > 0 && <div className="alert warn" style={{ marginTop: 20 }}><strong>{d.sellers_pending} seller{d.sellers_pending > 1 ? "s" : ""} waiting for approval.</strong> <Link href="/admin/sellers?status=pending">Review now →</Link></div>}
        <div className="grid g2" style={{ marginTop: 24 }}>
          <div className="card"><h3>Payment preference</h3><p className="muted small">Simulated preferences recorded on orders.</p>
            <Donut label="Payment preference" parts={[{ label: "Cash", value: d.payment_preference.cash ?? 0, color: "#8e8e93" }, { label: "Mobile Money", value: d.payment_preference.mobile_money ?? 0, color: "#0071e3" }]} /></div>
          <div className="card"><h3>Order value</h3><div className="stat">{afn(d.total_value_afn)}</div><p className="muted small">Total of non-cancelled orders (nothing is paid through the platform).</p></div>
        </div>
      </>)}
    </AdminShell>
  );
}
