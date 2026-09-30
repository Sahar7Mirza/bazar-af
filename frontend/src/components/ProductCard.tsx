import Link from "next/link";
import { afn } from "@/lib/format";
import type { Product } from "@/lib/types";

export function ProductCard({ p, emoji }: { p: Product; emoji: string }) {
  return (
    <Link href={`/products/${p.id}`} className="card hover prod">
      <div className="thumb" aria-hidden="true">{emoji}</div>
      <strong>{p.name}</strong>
      <span className="muted small">{p.seller_name}{p.district ? ` · ${p.district}` : ""}</span>
      <span className="price">{afn(p.price_afn)} <span className="muted small">/ {p.unit}</span></span>
      {p.stock_qty <= 0 ? <span className="chip bad">Out of stock</span> : p.stock_qty < 10 ? <span className="chip warn">Only {p.stock_qty} left</span> : null}
    </Link>
  );
}
