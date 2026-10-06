"use client";
import { AdminShell } from "@/components/AdminShell";
import { BarChart, Donut } from "@/components/charts";
import { Icon } from "@/components/Icon";
import { EmptyState, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";

interface Row { name: string; cash: number; mobile_money: number; total: number }
interface Week { week: string; cash: number; mobile_money: number; total: number }
interface Mkt {
  orders: number; preference: Record<string, number>; mobile_money_share_pct: number; providers: Record<string, number>;
  buyers: { total: number; mobile_money: number; share_pct: number }; weekly: Week[]; by_district: Row[]; by_category: Row[];
}
const pct = (r: Row) => (r.total ? Math.round((r.mobile_money / r.total) * 1000) / 10 : 0);

const share = (w: Week) => (w.total ? (w.mobile_money / w.total) * 100 : 0);
const MIN_WEEK = 5; // a week with fewer orders is too small to call a trend
function Delta({ diff, unit }: { diff: number; unit: string }) {
  const kind = Math.abs(diff) < 0.5 ? "flat" : diff > 0 ? "up" : "down";
  const sign = diff > 0 ? "+" : "";
  return <span className={`delta ${kind}`}><Icon name={kind === "flat" ? "flat" : kind === "up" ? "trend-up" : "trend-down"} size={14} /> {sign}{Math.round(diff * 10) / 10}{unit} vs previous week</span>;
}

/** Plain-language headlines computed from the same order data, so a reader sees the finding before the charts. */
function Insights({ d }: { d: Mkt }) {
  const w = d.weekly, last = w[w.length - 1], prev = w[w.length - 2];
  const best = [...d.by_category, ...d.by_district].sort((a, b) => pct(b) - pct(a))[0];
  const provider = Object.entries(d.providers).sort((a, b) => b[1] - a[1])[0];
  const mmOrders = d.preference.mobile_money ?? 0;
  return (
    <div className="grid g3s" style={{ marginTop: 16 }}>
      <div className="card insight"><span className="k"><Icon name="trend-up" size={16} /> Latest week</span>
        {last ? (<><p><strong>{Math.round(share(last))}%</strong> of orders in the week of {last.week} chose mobile money ({last.mobile_money} of {last.total}).</p>
          {prev && last.total >= MIN_WEEK && prev.total >= MIN_WEEK ? <Delta diff={share(last) - share(prev)} unit=" pts" /> : <span className="muted small">Too few orders to compare with the previous week (needs {MIN_WEEK}+ in each).</span>}</>) : <p className="muted">No weekly data yet.</p>}</div>
      <div className="card insight"><span className="k"><Icon name="wallet" size={16} /> Favourite provider</span>
        {provider ? <p><strong>{provider[0]}</strong> is used in {Math.round((provider[1] / Math.max(1, mmOrders)) * 100)}% of mobile-money orders ({provider[1]} of {mmOrders}).</p> : <p className="muted">No mobile-money orders yet.</p>}</div>
      <div className="card insight"><span className="k"><Icon name="trophy" size={16} /> Strongest segment</span>
        {best ? <p><strong>{best.name}</strong> leads with <strong>{pct(best)}%</strong> mobile money across {best.total} orders.</p> : <p className="muted">Segments appear once they have 5 or more orders.</p>}</div>
    </div>
  );
}

export default function Research() {
  const m = useLoad(() => api<Mkt>("admin/analytics/marketplace"), []);
  const d = m.data;
  return (
    <AdminShell title="Mobile money adoption">
      {m.loading ? <LoadingRows n={4} /> : m.error || !d ? <ErrorState error={m.error} retry={m.reload} /> : d.orders === 0 ? (
        <EmptyState icon="bag" title="No orders yet" text="Adoption figures appear here as buyers place orders and choose Cash or Mobile Money at checkout." />
      ) : (<>
        <p className="muted">Based on the payment preference buyers choose at checkout (cancelled orders excluded). No money moves on Bazar.af, so these are stated preferences, not payments.</p>
        <Insights d={d} />
        <div className="grid g3s" style={{ marginTop: 20 }}>
          <div className="card"><h3>Orders choosing mobile money</h3><div className="stat">{d.mobile_money_share_pct}%</div><p className="muted small">{d.preference.mobile_money ?? 0} of {d.orders} orders</p></div>
          <div className="card"><h3>Buyers using mobile money</h3><div className="stat">{d.buyers.share_pct}%</div><p className="muted small">{d.buyers.mobile_money} of {d.buyers.total} buyers chose it at least once</p></div>
          <div className="card"><h3>Cash vs Mobile Money</h3>
            <Donut label="Order payment preference" parts={[{ label: "Cash", value: d.preference.cash ?? 0, color: "#8e8e93" }, { label: "Mobile Money", value: d.preference.mobile_money ?? 0, color: "#0071e3" }]} /></div>
        </div>
        <div className="grid g2" style={{ marginTop: 20 }}>
          <div className="card"><h3>Which mobile-money provider?</h3>
            {Object.keys(d.providers).length === 0 ? <EmptyState icon="phone" title="No mobile-money orders yet" /> :
              <BarChart label="Orders by mobile money provider" max={Math.max(1, ...Object.values(d.providers))} data={Object.entries(d.providers).sort((a, b) => b[1] - a[1]).map(([label, value]) => ({ label, value }))} />}</div>
          <div className="card"><h3>Mobile-money share by week</h3><p className="muted small">Percent of that week’s orders (last 12 weeks).</p>
            {d.weekly.length === 0 ? <EmptyState icon="calendar" title="No weekly data yet" /> :
              <BarChart label="Mobile money share by week" max={100} unit="%" data={d.weekly.map((w) => ({ label: w.week, value: w.total ? Math.round((w.mobile_money / w.total) * 1000) / 10 : 0 }))} />}</div>
        </div>
        <div className="grid g2" style={{ marginTop: 20 }}>
          <div className="card"><h3>By seller district</h3><p className="muted small">Districts with at least 5 orders.</p>
            {d.by_district.length === 0 ? <EmptyState icon="map" title="Not enough orders per district yet" /> :
              <BarChart label="Mobile money share by district" max={100} unit="%" data={d.by_district.map((r) => ({ label: `${r.name} (${r.total})`, value: pct(r) }))} />}</div>
          <div className="card"><h3>By product category</h3><p className="muted small">Categories with at least 5 orders.</p>
            {d.by_category.length === 0 ? <EmptyState icon="tag" title="Not enough orders per category yet" /> :
              <BarChart label="Mobile money share by category" max={100} unit="%" data={d.by_category.map((r) => ({ label: `${r.name} (${r.total})`, value: pct(r) }))} />}</div>
        </div>
      </>)}
    </AdminShell>
  );
}
