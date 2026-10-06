"use client";
import { BarChart, Donut } from "@/components/charts";
import { Icon } from "@/components/Icon";
import { useLiveRefresh } from "@/components/Live";
import { EmptyState, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { afn } from "@/lib/format";

interface Row { name: string; cash: number; mobile_money: number; total: number; share_pct: number; ci_pct: [number, number] }
interface Week { week: string; cash: number; mobile_money: number; total: number }
interface Test { chi2: number; df: number; p: number; cramers_v: number; significant: boolean }
export interface Summary {
  orders: number; preference: Record<string, number>; mobile_money_share_pct: number; ci_pct: [number, number]; providers: Record<string, number>;
  avg_order_afn: Record<string, number>; buyers: { total: number; mobile_money: number; share_pct: number }; weekly: Week[]; by_district: Row[]; by_category: Row[];
  tests: { district: Test | null; category: Test | null }; period: { from: string | null; to: string | null }; min_cell: number; generated_at: string;
}

const share = (w: Week) => (w.total ? (w.mobile_money / w.total) * 100 : 0);
const MIN_WEEK = 5; // a week with fewer orders is too small to call a trend
const effect = (v: number) => (v < 0.1 ? "negligible" : v < 0.3 ? "small" : v < 0.5 ? "moderate" : "large");

function Delta({ diff, unit }: { diff: number; unit: string }) {
  const kind = Math.abs(diff) < 0.5 ? "flat" : diff > 0 ? "up" : "down";
  const sign = diff > 0 ? "+" : "";
  return <span className={`delta ${kind}`}><Icon name={kind === "flat" ? "flat" : kind === "up" ? "trend-up" : "trend-down"} size={14} /> {sign}{Math.round(diff * 10) / 10}{unit} vs previous week</span>;
}

/** Plain-language headlines computed from the same order data, so a reader sees the finding before the charts. */
function Insights({ d }: { d: Summary }) {
  const w = d.weekly, last = w[w.length - 1], prev = w[w.length - 2];
  const best = [...d.by_category, ...d.by_district].sort((a, b) => b.share_pct - a.share_pct)[0];
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
        {best ? <p><strong>{best.name}</strong> leads with <strong>{best.share_pct}%</strong> mobile money across {best.total} orders.</p> : <p className="muted">Segments appear once they have {d.min_cell} or more orders.</p>}</div>
    </div>
  );
}

function TestLine({ what, t }: { what: string; t: Test | null }) {
  if (!t) return <li><strong>{what}:</strong> <span className="muted">not enough orders yet to compare groups fairly.</span></li>;
  return (
    <li><strong>{what}:</strong> {t.significant ? `mobile-money use differs between groups, and it is unlikely to be chance` : "no clear difference between groups"}{" "}
      <span className="muted">(χ² = {t.chi2}, df = {t.df}, p {t.p < 0.001 ? "< 0.001" : `= ${t.p}`}; effect size {effect(t.cramers_v)}, V = {t.cramers_v})</span></li>
  );
}

export function ResearchView({ admin = false }: { admin?: boolean }) {
  const m = useLoad(() => api<Summary>(admin ? "admin/research/summary" : "research/summary"), [admin]);
  useLiveRefresh(m.refresh);
  const d = m.data;
  if (m.loading) return <LoadingRows n={4} />;
  if (m.error || !d) return <ErrorState error={m.error} retry={m.reload} />;
  if (d.orders === 0) return <EmptyState icon="bag" title="No orders yet" text="Adoption figures appear here as buyers place orders and choose Cash or Mobile Money at checkout." />;
  const mm = d.preference.mobile_money ?? 0;
  return (<>
    <div className="grid g3s">
      <div className="card"><h3>Orders choosing mobile money</h3><div className="stat">{d.mobile_money_share_pct}%</div>
        <p className="muted small">{mm} of {d.orders} orders. With 95% confidence the true share is between {d.ci_pct[0]}% and {d.ci_pct[1]}%.</p></div>
      <div className="card"><h3>Buyers using mobile money</h3><div className="stat">{d.buyers.share_pct}%</div><p className="muted small">{d.buyers.mobile_money} of {d.buyers.total} buyers chose it at least once</p></div>
      <div className="card"><h3>Cash vs Mobile Money</h3>
        <Donut label="Order payment preference" parts={[{ label: "Cash", value: d.preference.cash ?? 0, color: "#8e8e93" }, { label: "Mobile Money", value: mm, color: "#0071e3" }]} /></div>
    </div>
    <Insights d={d} />
    <div className="grid g2" style={{ marginTop: 20 }}>
      <div className="card"><h3>Which mobile-money provider?</h3>
        {Object.keys(d.providers).length === 0 ? <EmptyState icon="phone" title="No mobile-money orders yet" /> :
          <BarChart label="Orders by mobile money provider" max={Math.max(1, ...Object.values(d.providers))} data={Object.entries(d.providers).sort((a, b) => b[1] - a[1]).map(([label, value]) => ({ label, value }))} />}</div>
      <div className="card"><h3>Mobile-money share by week</h3><p className="muted small">Percent of that week’s orders (last 12 weeks).</p>
        {d.weekly.length === 0 ? <EmptyState icon="calendar" title="No weekly data yet" /> :
          <BarChart label="Mobile money share by week" max={100} unit="%" data={d.weekly.map((w) => ({ label: w.week, value: Math.round(share(w) * 10) / 10 }))} />}</div>
    </div>
    <div className="grid g2" style={{ marginTop: 20 }}>
      <div className="card"><h3>By seller district</h3><p className="muted small">{admin ? "Every district, with the number of orders in brackets." : `Districts with at least ${d.min_cell} orders.`}</p>
        {d.by_district.length === 0 ? <EmptyState icon="map" title="Not enough orders per district yet" /> :
          <BarChart label="Mobile money share by district" max={100} unit="%" data={d.by_district.map((r) => ({ label: `${r.name} (${r.total})`, value: r.share_pct }))} />}</div>
      <div className="card"><h3>By product category</h3><p className="muted small">{admin ? "Every category, with the number of orders in brackets." : `Categories with at least ${d.min_cell} orders.`}</p>
        {d.by_category.length === 0 ? <EmptyState icon="tag" title="Not enough orders per category yet" /> :
          <BarChart label="Mobile money share by category" max={100} unit="%" data={d.by_category.map((r) => ({ label: `${r.name} (${r.total})`, value: r.share_pct }))} />}</div>
    </div>
    <div className="grid g2" style={{ marginTop: 20 }}>
      <div className="card"><h3>Do mobile-money orders cost more?</h3>
        <p className="muted small">Average order value by payment choice.</p>
        <BarChart label="Average order value in AFN" max={Math.max(1, ...Object.values(d.avg_order_afn))} data={[{ label: "Cash", value: d.avg_order_afn.cash ?? 0 }, { label: "Mobile Money", value: d.avg_order_afn.mobile_money ?? 0 }]} unit=" AFN" />
        <p className="muted small" style={{ marginTop: 12 }}>Average basket: {afn(d.avg_order_afn.cash ?? 0)} for cash, {afn(d.avg_order_afn.mobile_money ?? 0)} for mobile money.</p></div>
      <div className="card"><h3>Is the difference real?</h3>
        <p className="muted small">A chi-square test asks whether groups differ more than chance would explain.</p>
        <ul className="stack small" style={{ paddingLeft: 18, margin: 0 }}><TestLine what="Across districts" t={d.tests.district} /><TestLine what="Across categories" t={d.tests.category} /></ul></div>
    </div>
    <div className="card" style={{ marginTop: 20 }}>
      <h3>How these numbers are made</h3>
      <ul className="small stack" style={{ paddingLeft: 18, margin: 0 }}>
        <li>Every order records the buyer’s choice at checkout: <strong>Cash</strong> or <strong>Mobile Money</strong> (and which provider). Cancelled orders are not counted.</li>
        <li>No money moves on Bazar.af, so these are <strong>stated preferences</strong>, not payments. They show willingness to use mobile money, not proof of paying with it.</li>
        <li>Shares come with a 95% confidence interval (Wilson). The fewer the orders, the wider the range, so read small groups with care.</li>
        <li>{admin ? "Admins see every group. The public page hides groups with fewer than 5 orders so nobody can be singled out." : "Groups with fewer than 5 orders are hidden so nobody can be singled out. No names, phone numbers or buyer IDs are ever shown."}</li>
        <li>The sample is people who use Bazar.af, not every shopper in Kabul. While the site runs on demo data, treat the figures as an example of what the study will measure.</li>
      </ul>
      <p className="muted small" style={{ marginTop: 12, marginBottom: 0 }}>{d.orders} orders{d.period.from ? ` from ${d.period.from} to ${d.period.to}` : ""} · updated {new Date(d.generated_at).toLocaleString()}</p>
    </div>
    {admin && <div className="row" style={{ marginTop: 20 }}><a className="btn" href="/api/proxy/admin/research/export.csv" download><Icon name="download" size={16} /> Download anonymised orders (CSV)</a><span className="muted small">One row per order: week, district, category, choice, provider, total. No names or IDs. Ready for Excel, SPSS or R.</span></div>}
  </>);
}
