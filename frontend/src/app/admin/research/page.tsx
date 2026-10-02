"use client";
import { AdminShell } from "@/components/AdminShell";
import { BarChart, Donut } from "@/components/charts";
import { EmptyState, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";

interface Row { name: string; cash: number; mobile_money: number; total: number }
interface Week { week: string; cash: number; mobile_money: number; total: number }
interface Mkt {
  orders: number; preference: Record<string, number>; mobile_money_share_pct: number; providers: Record<string, number>;
  buyers: { total: number; mobile_money: number; share_pct: number }; weekly: Week[]; by_district: Row[]; by_category: Row[];
}
const pct = (r: Row) => (r.total ? Math.round((r.mobile_money / r.total) * 1000) / 10 : 0);

export default function Research() {
  const m = useLoad(() => api<Mkt>("admin/analytics/marketplace"), []);
  const d = m.data;
  return (
    <AdminShell title="Mobile money adoption">
      {m.loading ? <LoadingRows n={4} /> : m.error || !d ? <ErrorState error={m.error} retry={m.reload} /> : d.orders === 0 ? (
        <EmptyState emoji="🛍️" title="No orders yet" text="Adoption figures appear here as buyers place orders and choose Cash or Mobile Money at checkout." />
      ) : (<>
        <p className="muted">Based on the payment preference buyers choose at checkout (cancelled orders excluded). No money moves on Bazar.af, so these are stated preferences, not payments.</p>
        <div className="grid g3" style={{ marginTop: 16 }}>
          <div className="card"><h3>Orders choosing mobile money</h3><div className="stat">{d.mobile_money_share_pct}%</div><p className="muted small">{d.preference.mobile_money ?? 0} of {d.orders} orders</p></div>
          <div className="card"><h3>Buyers using mobile money</h3><div className="stat">{d.buyers.share_pct}%</div><p className="muted small">{d.buyers.mobile_money} of {d.buyers.total} buyers chose it at least once</p></div>
          <div className="card"><h3>Cash vs Mobile Money</h3>
            <Donut label="Order payment preference" parts={[{ label: "Cash", value: d.preference.cash ?? 0, color: "#8e8e93" }, { label: "Mobile Money", value: d.preference.mobile_money ?? 0, color: "#0071e3" }]} /></div>
        </div>
        <div className="grid g2" style={{ marginTop: 20 }}>
          <div className="card"><h3>Which mobile-money provider?</h3>
            {Object.keys(d.providers).length === 0 ? <EmptyState emoji="📱" title="No mobile-money orders yet" /> :
              <BarChart label="Orders by mobile money provider" max={Math.max(1, ...Object.values(d.providers))} data={Object.entries(d.providers).sort((a, b) => b[1] - a[1]).map(([label, value]) => ({ label, value }))} />}</div>
          <div className="card"><h3>Mobile-money share by week</h3><p className="muted small">Percent of that week’s orders (last 12 weeks).</p>
            {d.weekly.length === 0 ? <EmptyState emoji="📅" title="No weekly data yet" /> :
              <BarChart label="Mobile money share by week" max={100} unit="%" data={d.weekly.map((w) => ({ label: w.week, value: w.total ? Math.round((w.mobile_money / w.total) * 1000) / 10 : 0 }))} />}</div>
        </div>
        <div className="grid g2" style={{ marginTop: 20 }}>
          <div className="card"><h3>By seller district</h3><p className="muted small">Districts with at least 5 orders.</p>
            {d.by_district.length === 0 ? <EmptyState emoji="🗺️" title="Not enough orders per district yet" /> :
              <BarChart label="Mobile money share by district" max={100} unit="%" data={d.by_district.map((r) => ({ label: `${r.name} (${r.total})`, value: pct(r) }))} />}</div>
          <div className="card"><h3>By product category</h3><p className="muted small">Categories with at least 5 orders.</p>
            {d.by_category.length === 0 ? <EmptyState emoji="🏷️" title="Not enough orders per category yet" /> :
              <BarChart label="Mobile money share by category" max={100} unit="%" data={d.by_category.map((r) => ({ label: `${r.name} (${r.total})`, value: pct(r) }))} />}</div>
        </div>
      </>)}
    </AdminShell>
  );
}
