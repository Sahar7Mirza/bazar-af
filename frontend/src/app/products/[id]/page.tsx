"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useSession } from "@/components/Session";
import { Alert, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { cart } from "@/lib/cart";
import { Icon, categoryIcon } from "@/components/Icon";
import { Similar } from "@/components/Recommended";
import { afn } from "@/lib/format";
import type { Category, Product } from "@/lib/types";

export default function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useSession();
  const [qty, setQty] = useState(1);
  const [msg, setMsg] = useState<{ kind: "ok" | "bad"; text: string } | null>(null);
  const p = useLoad(() => api<Product>(`products/${id}`), [id]);
  const cats = useLoad(() => api<Category[]>("categories"), []);
  if (p.loading) return <div className="wrap page"><LoadingRows n={4} /></div>;
  if (p.error || !p.data) return <div className="wrap page"><ErrorState error={p.error} retry={p.reload} /></div>;
  const d = p.data;
  const cat = cats.data?.find((c) => c.id === d.category_id)?.name;
  const canBuy = !user || user.role === "buyer";
  function add() {
    const r = cart.add({ productId: d.id, name: d.name, price: d.price_afn, unit: d.unit, sellerId: d.seller_id, sellerName: d.seller_name ?? "Seller", max: d.stock_qty }, qty);
    setMsg(r.ok ? { kind: "ok", text: "Added to your cart." } : { kind: "bad", text: "Your cart has items from another seller. Orders can include one seller only — finish or clear your cart first." });
  }
  return (
    <div className="wrap page">
      <p className="small"><Link href="/products">← All products</Link></p>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: 40, alignItems: "start" }}>
        <div className="thumb" style={{ aspectRatio: "1" }} aria-hidden="true"><Icon name={categoryIcon(cat)} size={96} /></div>
        <div>
          {cat && <p className="eyebrow">{cat}</p>}
          <h1 style={{ fontSize: "2.4rem" }}>{d.name}</h1>
          <p className="muted">Sold by <strong>{d.seller_name}</strong>{d.district ? ` · ${d.district}` : ""}</p>
          <p className="price" style={{ fontSize: "1.8rem" }}>{afn(d.price_afn)} <span className="muted small">/ {d.unit}</span></p>
          {d.description && <p>{d.description}</p>}
          <p>{d.stock_qty > 0 ? <span className="chip ok">{d.stock_qty} in stock</span> : <span className="chip bad">Out of stock</span>}</p>
          {msg && <Alert kind={msg.kind}>{msg.text} {msg.kind === "ok" && <Link href="/cart">View cart</Link>}</Alert>}
          {canBuy ? (
            <div className="row">
              <div style={{ width: 110 }}><label className="sr" htmlFor="qty">Quantity</label><input id="qty" type="number" min={1} max={d.stock_qty} value={qty} onChange={(e) => setQty(Math.max(1, Math.min(d.stock_qty || 1, Number(e.target.value) || 1)))} /></div>
              <button className="btn lg" disabled={d.stock_qty <= 0} onClick={add}>Add to cart</button>
              <button className="btn lg ghost" disabled={d.stock_qty <= 0} onClick={() => { add(); router.push("/cart"); }}>Buy now</button>
            </div>
          ) : <Alert>Sign in as a buyer to place orders.</Alert>}
          <p className="muted small" style={{ marginTop: 16 }}>Payment is arranged directly with the seller. Bazar.af records your preference only.</p>
        </div>
      </div>
      <Similar productId={d.id} />
    </div>
  );
}
