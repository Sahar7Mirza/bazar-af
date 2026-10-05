"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useSession } from "@/components/Session";
import { Alert, EmptyState, Field, Guard } from "@/components/ui";
import { api, ApiError, fieldErrors } from "@/lib/api";
import { cart, cartTotal, useCart } from "@/lib/cart";
import { afn } from "@/lib/format";
import { PROVIDERS, type Order } from "@/lib/types";

export default function Checkout() {
  const { user, loading } = useSession();
  const lines = useCart();
  const router = useRouter();
  const [pref, setPref] = useState<"cash" | "mobile_money">("cash");
  const [provider, setProvider] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  async function place() {
    setErr(null); setErrs({});
    if (pref === "mobile_money" && !provider) { setErrs({ mobile_money_provider: "Choose a provider" }); return; }
    setBusy(true);
    try {
      const o = await api<Order>("orders", { method: "POST", body: { items: lines.map((l) => ({ product_id: l.productId, quantity: l.qty })), payment_preference: pref, mobile_money_provider: pref === "mobile_money" ? provider : null, buyer_note: note || null } });
      cart.clear();
      router.push(`/orders/${o.id}?placed=1`);
    } catch (x) { setErrs(fieldErrors(x)); setErr(x instanceof ApiError ? x.message : "Could not place the order"); } finally { setBusy(false); }
  }
  return (
    <Guard roles={["buyer"]} user={user} loading={loading}>
      <div className="mid page">
        <h1 style={{ fontSize: "2.4rem" }}>Checkout</h1>
        {!lines.length ? <EmptyState icon="cart" title="Nothing to check out" action={<Link className="btn" href="/products">Browse products</Link>} /> : (<>
          {err && <Alert kind="bad">{err}</Alert>}
          <div className="card stack">
            <h3>Order summary · {lines[0].sellerName}</h3>
            {lines.map((l) => <div key={l.productId} className="row between"><span>{l.qty} × {l.name}</span><span>{afn(Number(l.price) * l.qty)}</span></div>)}
            <div className="row between"><strong>Total</strong><strong>{afn(cartTotal(lines))}</strong></div>
          </div>
          <h3 style={{ marginTop: 32 }}>How would you like to pay?</h3>
          <Alert>This is a <strong>preference only</strong>. No money is taken on Bazar.af — you settle with the seller directly.</Alert>
          <fieldset style={{ border: 0, padding: 0, margin: 0 }}><legend className="sr">Payment preference</legend>
            <div className="opt"><input type="radio" id="p-cash" name="pref" checked={pref === "cash"} onChange={() => setPref("cash")} /><label htmlFor="p-cash">Cash <span className="muted small">— pay in person</span></label></div>
            <div className="opt"><input type="radio" id="p-mm" name="pref" checked={pref === "mobile_money"} onChange={() => setPref("mobile_money")} /><label htmlFor="p-mm">Mobile Money <span className="muted small">— arrange with your provider</span></label></div>
          </fieldset>
          {pref === "mobile_money" && <Field id="prov" label="Provider" error={errs.mobile_money_provider}><select id="prov" value={provider} onChange={(e) => setProvider(e.target.value)} aria-invalid={!!errs.mobile_money_provider}><option value="">Select…</option>{PROVIDERS.map((p) => <option key={p}>{p}</option>)}</select></Field>}
          <Field id="note" label="Note for the seller (optional)"><textarea id="note" maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} /></Field>
          <button className="btn lg" style={{ width: "100%" }} disabled={busy} onClick={place}>{busy ? "Placing order…" : `Place order · ${afn(cartTotal(lines))}`}</button>
        </>)}
      </div>
    </Guard>
  );
}
