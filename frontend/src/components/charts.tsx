"use client";
/** Small dependency-free SVG charts. Each has a text/table alternative next to it for accessibility. */
export function BarChart({ data, max, label, unit = "" }: { data: { label: string; value: number }[]; max: number; label: string; unit?: string }) {
  return (
    <div role="img" aria-label={`${label}: ${data.map((d) => `${d.label} ${d.value}${unit}`).join(", ")}`} className="stack" style={{ marginTop: 12 }}>
      {data.map((d) => (
        <div key={d.label}>
          <div className="row between small"><span>{d.label}</span><strong>{d.value}{unit}</strong></div>
          <div className="bar"><span style={{ width: `${Math.max(2, (d.value / max) * 100)}%` }} /></div>
        </div>
      ))}
    </div>
  );
}
export function Donut({ parts, label }: { parts: { label: string; value: number; color: string }[]; label: string }) {
  const total = parts.reduce((s, p) => s + p.value, 0) || 1;
  const R = 54, C = 2 * Math.PI * R;
  const offsets = parts.map((_, i) => parts.slice(0, i).reduce((s, p) => s + (p.value / total) * C, 0));
  return (
    <div className="row" style={{ gap: 24 }}>
      <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={`${label}: ${parts.map((p) => `${p.label} ${Math.round((p.value / total) * 100)}%`).join(", ")}`}>
        <g transform="rotate(-90 70 70)">{parts.map((p, i) => { const len = (p.value / total) * C; return <circle key={p.label} cx="70" cy="70" r={R} fill="none" stroke={p.color} strokeWidth="18" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-offsets[i]} />; })}</g>
      </svg>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>{parts.map((p) => <li key={p.label}><span style={{ display: "inline-block", width: 12, height: 12, borderRadius: 3, background: p.color, marginRight: 8 }} />{p.label}: <strong>{p.value}</strong> ({Math.round((p.value / total) * 100)}%)</li>)}</ul>
    </div>
  );
}
export function Heatmap({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const color = (v: number) => (v >= 0 ? `color-mix(in srgb, var(--brand) ${Math.round(Math.abs(v) * 85)}%, transparent)` : `color-mix(in srgb, var(--bad) ${Math.round(Math.abs(v) * 85)}%, transparent)`);
  return (
    <div className="heat" style={{ gridTemplateColumns: `auto repeat(${labels.length}, 1fr)` }} role="table" aria-label="Correlation matrix of construct scores">
      <div />{labels.map((l) => <div key={l} role="columnheader"><strong>{l}</strong></div>)}
      {matrix.map((row, i) => [<div key={labels[i]} role="rowheader"><strong>{labels[i]}</strong></div>, ...row.map((v, j) => <div key={`${i}-${j}`} role="cell" style={{ background: color(v) }}>{v.toFixed(2)}</div>)])}
    </div>
  );
}
