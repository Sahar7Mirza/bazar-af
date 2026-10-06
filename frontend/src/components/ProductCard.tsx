import Link from "next/link";
import { Icon } from "@/components/Icon";
import { afn } from "@/lib/format";
import type { Product } from "@/lib/types";

/** Small bar showing how strongly a recommendation matches the buyer. Text label so it never relies on colour alone. */
export function MatchMeter({ value }: { value: number }) {
  const label = value >= 60 ? "Strong match" : value >= 35 ? "Good match" : "Light match";
  return (
    <span className="meter" role="img" aria-label={`${label}, ${value} percent`}>
      <span className="meter-bar"><span style={{ width: `${Math.max(6, value)}%` }} /></span>
      <span className="meter-l">{label}</span>
    </span>
  );
}

export function ProductCard({ p, icon, why, match }: { p: Product; icon: string; why?: string; match?: number }) {
  return (
    <Link href={`/products/${p.id}`} className="card hover prod">
      <div className="thumb" aria-hidden="true"><Icon name={icon} size={40} /></div>
      {why && <span className="why"><Icon name="sparkles" size={13} /> {why}</span>}
      {why && match !== undefined && <MatchMeter value={match} />}
      <strong>{p.name}</strong>
      <span className="muted small">{p.seller_name}{p.district ? ` · ${p.district}` : ""}</span>
      <span className="price">{afn(p.price_afn)} <span className="muted small">/ {p.unit}</span></span>
      {p.stock_qty <= 0 ? <span className="chip bad">Out of stock</span> : p.stock_qty < 10 ? <span className="chip warn">Only {p.stock_qty} left</span> : null}
    </Link>
  );
}
