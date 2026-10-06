"use client";
import Link from "next/link";
import { useState } from "react";
import { useSession } from "@/components/Session";
import { useLiveRefresh } from "@/components/Live";
import { Icon } from "@/components/Icon";
import { EmptyState, ErrorState, Guard, LoadingRows, Pager, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { AppNotification, Page } from "@/lib/types";

const KIND_ICON: Record<string, string> = { new_order: "bag", order_confirmed: "check", order_ready: "package-check", order_cancelled: "package-x", new_product: "sparkles" };

export default function Notifications() {
  const { user, loading } = useSession();
  const [page, setPage] = useState(1);
  const res = useLoad(() => api<Page<AppNotification>>("notifications", { query: { page, page_size: 10 } }), [page]);
  useLiveRefresh(res.refresh);
  async function open(n: AppNotification) {
    if (!n.read_at) { await api(`notifications/${n.id}/read`, { method: "POST" }).catch(() => {}); res.reload(); }
  }
  async function readAll() { await api("notifications/read-all", { method: "POST" }).catch(() => {}); res.reload(); }
  const anyUnread = res.data?.items.some((n) => !n.read_at);
  return (
    <Guard roles={["buyer", "seller", "admin"]} user={user} loading={loading}>
      <div className="mid page">
        <div className="row between"><h1 style={{ fontSize: "2.2rem" }}>Notifications</h1>{anyUnread && <button className="btn quiet sm" onClick={readAll}>Mark all as read</button>}</div>
        {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? (
          <EmptyState icon="bell" title="No notifications yet" text="You will be told here when a seller confirms your order, when it is ready for pick up, if it is cancelled, or when something new appears in a category you follow." />
        ) : (<>
          <div className="stack">{res.data.items.map((n) => (
            <div key={n.id} className={`card notif ${n.read_at ? "" : "unread"}`} onClick={() => open(n)}>
              <h3><Icon name={KIND_ICON[n.kind] ?? "bell"} size={16} className="kind" /> {n.title}</h3>
              <p>{n.message}</p>
              <div className="row between small muted"><span>{dateTime(n.created_at)}</span>{n.order_id ? <Link href={`/orders/${n.order_id}`} onClick={() => open(n)}>View order #{n.order_id}</Link> : n.product_id ? <Link href={`/products/${n.product_id}`} onClick={() => open(n)}>View product</Link> : null}</div>
            </div>))}
          </div>
          <Pager page={res.data} onPage={setPage} />
        </>)}
      </div>
    </Guard>
  );
}
