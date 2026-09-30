"use client";
import { useState } from "react";
import { AdminShell } from "@/components/AdminShell";
import { BarChart, Donut, Heatmap } from "@/components/charts";
import { Alert, EmptyState, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { DISTRICTS } from "@/lib/types";

interface Summary { total: number; valid: number; invalid: number; invalid_reasons: Record<string, number>; target: number; progress_pct: number; by_respondent_type: Record<string, number>; synthetic: number; uses_mobile_money: { yes: number; no: number } }
interface Desc { n: number; items: { construct: string; label: string; n: number; mean: number; sd: number | null; median: number }[] }
interface Rel { items: { construct: string; label: string; items: number; alpha: number | null; acceptable: boolean }[] }
interface Corr { ready: boolean; n: number; constructs?: string[]; pearson?: number[][]; p_values?: number[][] }
interface Reg { ready: boolean; n: number; min_n?: number; r2?: number; adj_r2?: number; f?: number; f_p?: number; summary?: string; coefficients?: { construct: string; label: string; b: number; beta: number; p: number; ci_low: number; ci_high: number; vif: number; significant: boolean }[] }
interface Mkt { orders: number; preference: Record<string, number>; mobile_money_share_pct: number; providers: Record<string, number>; by_category: { name: string; cash: number; mobile_money: number; total: number }[] }

export default function Research() {
  const [rtype, setRtype] = useState(""), [district, setDistrict] = useState("");
  const q = { respondent_type: rtype, district };
  const sum = useLoad(() => api<Summary>("admin/research/summary"), []);
  const desc = useLoad(() => api<Desc>("admin/research/descriptives", { query: q }), [rtype, district]);
  const rel = useLoad(() => api<Rel>("admin/research/reliability", { query: q }), [rtype, district]);
  const cor = useLoad(() => api<Corr>("admin/research/correlations", { query: q }), [rtype, district]);
  const reg = useLoad(() => api<Reg>("admin/research/regression", { query: q }), [rtype, district]);
  const mkt = useLoad(() => api<Mkt>("admin/analytics/marketplace"), []);
  const s = sum.data;
  return (
    <AdminShell title="Mobile money research">
      {sum.loading ? <LoadingRows n={3} /> : sum.error || !s ? <ErrorState error={sum.error} retry={sum.reload} /> : (<>
        {s.synthetic > 0 && <Alert kind="warn"><strong>Demo data.</strong> {s.synthetic} of {s.total} responses are synthetic seed data for demonstration. Clear the survey tables before collecting real answers.</Alert>}
        <div className="grid g2">
          <div className="card"><h3>Responses</h3><div className="stat">{s.valid} <span className="muted" style={{ fontSize: "1rem" }}>/ {s.target} target</span></div>
            <div className="bar" role="progressbar" aria-valuenow={s.progress_pct} aria-valuemin={0} aria-valuemax={100} aria-label="Progress towards target"><span style={{ width: `${s.progress_pct}%` }} /></div>
            <p className="muted small" style={{ marginTop: 10 }}>{s.invalid} excluded {s.invalid ? `(${Object.entries(s.invalid_reasons).map(([k, v]) => `${k.replace("_", " ")}: ${v}`).join(", ")})` : ""}</p></div>
          <div className="card"><h3>Who answered</h3><Donut label="Respondent types" parts={[{ label: "Sellers", value: s.by_respondent_type.seller ?? 0, color: "#0071e3" }, { label: "Buyers", value: s.by_respondent_type.buyer ?? 0, color: "#34c759" }, { label: "Other", value: s.by_respondent_type.other ?? 0, color: "#8e8e93" }]} /></div>
        </div>
        <div className="row" style={{ margin: "28px 0 16px" }}>
          <strong>Filter analysis:</strong>
          <div><label className="sr" htmlFor="f-t">Respondent type</label><select id="f-t" style={{ width: "auto" }} value={rtype} onChange={(e) => setRtype(e.target.value)}><option value="">All respondents</option><option value="seller">Sellers</option><option value="buyer">Buyers</option><option value="other">Other</option></select></div>
          <div><label className="sr" htmlFor="f-d">District</label><select id="f-d" style={{ width: "auto" }} value={district} onChange={(e) => setDistrict(e.target.value)}><option value="">All districts</option>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select></div>
          <a className="btn quiet sm" href="/api/proxy/admin/research/export.csv" download>Export CSV</a>
        </div>
        <div className="grid g2">
          <div className="card"><h3>Average score by construct</h3><p className="muted small">Mean of 1–5 agreement scores{desc.data ? ` (n = ${desc.data.n})` : ""}.</p>
            {desc.loading ? <LoadingRows n={3} /> : desc.error ? <ErrorState error={desc.error} retry={desc.reload} /> : !desc.data?.items.length ? <EmptyState emoji="📊" title="No responses match these filters" /> :
              <BarChart label="Average score by construct" max={5} data={desc.data.items.map((d) => ({ label: d.label, value: d.mean }))} />}</div>
          <div className="card"><h3>Scale reliability</h3><p className="muted small">Cronbach’s α — 0.70 or higher is acceptable.</p>
            {rel.loading ? <LoadingRows n={3} /> : rel.error ? <ErrorState error={rel.error} retry={rel.reload} /> : !rel.data?.items.length ? <EmptyState emoji="📐" title="Not enough data" /> :
              <div className="table-wrap" style={{ border: 0 }}><table><thead><tr><th>Construct</th><th className="num">Items</th><th className="num">α</th></tr></thead><tbody>{rel.data.items.map((r) => <tr key={r.construct}><td>{r.label}</td><td className="num">{r.items}</td><td className="num">{r.alpha ?? "—"} {r.alpha !== null && <span className={`chip ${r.acceptable ? "ok" : "warn"}`}>{r.acceptable ? "good" : "low"}</span>}</td></tr>)}</tbody></table></div>}</div>
        </div>
        <div className="card" style={{ marginTop: 20 }}><h3>What drives willingness to adopt?</h3>
          {reg.loading ? <LoadingRows n={3} /> : reg.error ? <ErrorState error={reg.error} retry={reg.reload} /> : !reg.data?.ready ? <EmptyState emoji="🧮" title="Not enough responses for regression yet" text={`Need at least ${reg.data?.min_n ?? 30} valid responses (have ${reg.data?.n ?? 0}).`} /> : (<>
            <Alert kind="info">{reg.data.summary}</Alert>
            <p className="muted small">OLS regression of Willingness to adopt on the five predictors · n = {reg.data.n} · R² = {reg.data.r2} (adj. {reg.data.adj_r2}) · F = {reg.data.f}, p {reg.data.f_p! < 0.001 ? "< 0.001" : `= ${reg.data.f_p}`}</p>
            <div className="table-wrap"><table><thead><tr><th>Predictor</th><th className="num">b</th><th className="num">β</th><th className="num">95% CI</th><th className="num">p</th><th className="num">VIF</th></tr></thead>
              <tbody>{reg.data.coefficients!.map((c) => <tr key={c.construct}><td>{c.label} {c.significant && <span className="chip ok">significant</span>}</td><td className="num">{c.b}</td><td className="num">{c.beta}</td><td className="num">[{c.ci_low}, {c.ci_high}]</td><td className="num">{c.p < 0.001 ? "< 0.001" : c.p}</td><td className="num">{c.vif}</td></tr>)}</tbody></table></div>
            <h3 style={{ marginTop: 20 }}>Standardised effect (β)</h3>
            <BarChart label="Standardised beta by predictor" max={Math.max(0.5, ...reg.data.coefficients!.map((c) => Math.abs(c.beta)))} data={reg.data.coefficients!.map((c) => ({ label: c.label, value: c.beta }))} />
          </>)}</div>
        <div className="grid g2" style={{ marginTop: 20 }}>
          <div className="card"><h3>Correlations</h3><p className="muted small">Pearson r between construct scores.</p>
            {cor.loading ? <LoadingRows n={3} /> : cor.error ? <ErrorState error={cor.error} retry={cor.reload} /> : !cor.data?.ready ? <EmptyState emoji="🔗" title="Not enough data" /> : <Heatmap labels={cor.data.constructs!} matrix={cor.data.pearson!} />}</div>
          <div className="card"><h3>Marketplace: stated payment preference</h3>
            {mkt.loading ? <LoadingRows n={3} /> : mkt.error || !mkt.data ? <ErrorState error={mkt.error} retry={mkt.reload} /> : mkt.data.orders === 0 ? <EmptyState emoji="🛍️" title="No orders yet" /> : (<>
              <Donut label="Order payment preference" parts={[{ label: "Cash", value: mkt.data.preference.cash ?? 0, color: "#8e8e93" }, { label: "Mobile Money", value: mkt.data.preference.mobile_money ?? 0, color: "#0071e3" }]} />
              <p className="muted small" style={{ marginTop: 12 }}>{mkt.data.mobile_money_share_pct}% of {mkt.data.orders} orders chose mobile money. Providers: {Object.entries(mkt.data.providers).map(([k, v]) => `${k} ${v}`).join(" · ") || "—"}</p></>)}</div>
        </div>
      </>)}
    </AdminShell>
  );
}
