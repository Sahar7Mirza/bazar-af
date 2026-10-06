"use client";
import Link from "next/link";
import { useState } from "react";
import { useLiveRefresh } from "@/components/Live";
import { EmptyState, ErrorState, LoadingRows, Pager, StatusChip, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { afn, dateTime, pref } from "@/lib/format";
import type { Order, Page } from "@/lib/types";

const FILTERS = ["", "pending", "confirmed", "ready", "completed", "cancelled"];
const LABEL: Record<string, string> = { "": "All", pending: "Pending", confirmed: "Confirmed", ready: "Ready", completed: "Completed", cancelled: "Cancelled" };
export function OrderTable({ endpoint = "orders", showBuyer = false }: { endpoint?: string; showBuyer?: boolean }) {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const res = useLoad(() => api<Page<Order>>(endpoint, { query: { status, page, page_size: 10 } }), [status, page, endpoint]);
  useLiveRefresh(res.refresh);  // a new order or status change shows up here by itself
  const counts = res.data?.counts ?? {};
  return (
    <div>
      <div className="seg" role="group" aria-label="Filter orders by status" style={{ marginBottom: 16 }}>
        {FILTERS.map((s) => {
          const n = s ? counts[s] : Object.values(counts).reduce((a, b) => a + b, 0);
          return (
            <button key={s} type="button" aria-pressed={status === s} onClick={() => { setStatus(s); setPage(1); }}>
              {LABEL[s]}{res.data?.counts ? <span className="n">{n}</span> : null}
            </button>
          );
        })}
      </div>
      {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? (
        <EmptyState icon="package" title="No orders yet" text={status ? "No orders with this status." : "Orders will show up here."} />
      ) : (<>
        <div className="table-wrap"><table>
          <thead><tr><th>Order</th><th>Date</th>{showBuyer && <th>Buyer</th>}<th>Payment preference</th><th>Status</th><th className="num">Total</th></tr></thead>
          <tbody>{res.data.items.map((o) => (
            <tr key={o.id}><td><Link href={`/orders/${o.id}`}>#{o.id}</Link></td><td>{dateTime(o.created_at)}</td>{showBuyer && <td>#{o.buyer_id}</td>}
              <td>{pref(o.payment_preference, o.mobile_money_provider)}</td><td><StatusChip status={o.status} /></td><td className="num">{afn(o.total_afn)}</td></tr>))}</tbody>
        </table></div>
        <Pager page={res.data} onPage={setPage} />
      </>)}
    </div>
  );
}
