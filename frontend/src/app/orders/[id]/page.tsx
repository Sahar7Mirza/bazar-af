"use client";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useSession } from "@/components/Session";
import { Alert, ErrorState, Guard, LoadingRows, StatusChip, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { afn, dateTime, pref } from "@/lib/format";
import type { Order } from "@/lib/types";

const NEXT: Record<string, [string, string] | undefined> = { pending: ["confirmed", "Confirm order"], confirmed: ["ready", "Mark ready"], ready: ["completed", "Mark completed"] };
const FLOW = ["pending", "confirmed", "ready", "completed"];

function Detail() {
  const { id } = useParams<{ id: string }>();
  const placed = useSearchParams().get("placed");
  const { user, loading } = useSession();
  const o = useLoad(() => api<Order>(`orders/${id}`), [id]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  async function act(path: string, body: unknown) {
    setBusy(true); setErr(null);
    try { await api(`orders/${id}/${path}`, { method: "POST", body }); o.reload(); } catch (x) { setErr(x instanceof ApiError ? x.message : "Action failed"); } finally { setBusy(false); }
  }
  return (
    <Guard roles={["buyer", "seller", "admin"]} user={user} loading={loading}>
      <div className="mid page">
        <p className="small"><Link href={user?.role === "admin" ? "/admin/orders" : "/orders"}>← Orders</Link></p>
        {o.loading ? <LoadingRows n={4} /> : o.error || !o.data ? <ErrorState error={o.error} retry={o.reload} /> : (() => {
          const d = o.data, isSeller = user?.role === "seller", next = isSeller ? NEXT[d.status] : undefined;
          const canCancel = (user?.role === "buyer" && d.status === "pending") || (isSeller && ["pending", "confirmed", "ready"].includes(d.status));
          return (<>
            {placed && <Alert kind="ok"><strong>Order placed.</strong> The seller will confirm it soon. Remember: no payment was taken — settle with the seller.</Alert>}
            {err && <Alert kind="bad">{err}</Alert>}
            <div className="row between"><h1 style={{ fontSize: "2.2rem" }}>Order #{d.id}</h1><StatusChip status={d.status} /></div>
            {d.status !== "cancelled" && <div className="steps" role="img" aria-label={`Progress: ${d.status}`}>{FLOW.map((s, i) => <span key={s} className={i <= FLOW.indexOf(d.status) ? "on" : ""} />)}</div>}
            <div className="card stack">
              <div className="row between"><span className="muted">Placed</span><span>{dateTime(d.created_at)}</span></div>
              <div className="row between"><span className="muted">Payment preference</span><strong>{pref(d.payment_preference, d.mobile_money_provider)}</strong></div>
              <div className="row between"><span className="muted">Payment status</span><span className="chip">Not processed (simulated)</span></div>
              {d.buyer_note && <div><span className="muted">Buyer note</span><p>{d.buyer_note}</p></div>}
              {d.cancel_reason && <div><span className="muted">Cancellation reason</span><p>{d.cancel_reason}</p></div>}
            </div>
            <div className="table-wrap" style={{ marginTop: 20 }}><table>
              <thead><tr><th>Item</th><th className="num">Price</th><th className="num">Qty</th><th className="num">Total</th></tr></thead>
              <tbody>{d.items.map((i) => <tr key={i.product_id}><td>{i.product_name}</td><td className="num">{afn(i.unit_price_afn)}</td><td className="num">{i.quantity}</td><td className="num">{afn(i.line_total_afn)}</td></tr>)}
                <tr><td colSpan={3}><strong>Total</strong></td><td className="num"><strong>{afn(d.total_afn)}</strong></td></tr></tbody>
            </table></div>
            {(next || canCancel) && (
              <div className="card" style={{ marginTop: 20 }}>
                <div className="row">
                  {next && <button className="btn" disabled={busy} onClick={() => act("status", { status: next[0] })}>{next[1]}</button>}
                  {canCancel && <><label className="sr" htmlFor="why">Reason</label><input id="why" style={{ flex: 1, minWidth: 180 }} placeholder="Reason (optional)" value={reason} onChange={(e) => setReason(e.target.value)} /><button className="btn danger" disabled={busy} onClick={() => act("cancel", { reason: reason || null })}>Cancel order</button></>}
                </div>
              </div>
            )}
          </>);
        })()}
      </div>
    </Guard>
  );
}
export default function OrderPage() { return <Suspense><Detail /></Suspense>; }
