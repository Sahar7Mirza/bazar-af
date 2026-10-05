"use client";
import Link from "next/link";
import { EmptyState } from "@/components/ui";
import { cart, cartTotal, useCart } from "@/lib/cart";
import { afn } from "@/lib/format";

export default function Cart() {
  const lines = useCart();
  if (!lines.length) return <div className="wrap page"><EmptyState icon="cart" title="Your cart is empty" text="Find something you like from a local seller." action={<Link className="btn" href="/products">Browse products</Link>} /></div>;
  return (
    <div className="wrap page">
      <h1 style={{ fontSize: "2.4rem" }}>Your cart</h1>
      <p className="muted">From <strong>{lines[0].sellerName}</strong></p>
      <div className="table-wrap"><table>
        <thead><tr><th>Product</th><th className="num">Price</th><th>Qty</th><th className="num">Total</th><th><span className="sr">Remove</span></th></tr></thead>
        <tbody>{lines.map((l) => (
          <tr key={l.productId}>
            <td><Link href={`/products/${l.productId}`}>{l.name}</Link></td><td className="num">{afn(l.price)}</td>
            <td style={{ width: 110 }}><label className="sr" htmlFor={`q${l.productId}`}>Quantity for {l.name}</label><input id={`q${l.productId}`} type="number" min={1} max={l.max} value={l.qty} onChange={(e) => cart.setQty(l.productId, Number(e.target.value) || 1)} /></td>
            <td className="num">{afn(Number(l.price) * l.qty)}</td><td><button className="link" onClick={() => cart.remove(l.productId)} aria-label={`Remove ${l.name}`}>Remove</button></td>
          </tr>))}</tbody>
      </table></div>
      <div className="row between" style={{ marginTop: 24 }}>
        <button className="link" onClick={() => cart.clear()}>Clear cart</button>
        <div className="row"><span className="stat" style={{ fontSize: "1.6rem" }}>{afn(cartTotal(lines))}</span><Link className="btn lg" href="/checkout">Checkout</Link></div>
      </div>
    </div>
  );
}
