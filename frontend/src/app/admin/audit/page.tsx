"use client";
import { useState } from "react";
import { AdminShell } from "@/components/AdminShell";
import { EmptyState, ErrorState, LoadingRows, Pager, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { Page } from "@/lib/types";

interface Row { id: number; actor_id: number | null; action: string; entity_type: string | null; entity_id: string | null; detail: Record<string, unknown> | null; request_id: string | null; created_at: string }
export default function Audit() {
  const [page, setPage] = useState(1), [action, setAction] = useState("");
  const res = useLoad(() => api<Page<Row>>("admin/audit", { query: { action, page, page_size: 20 } }), [action, page]);
  return (
    <AdminShell title="Audit log">
      <div className="row" style={{ marginBottom: 16 }}><label className="sr" htmlFor="act">Filter by action</label><input id="act" style={{ maxWidth: 260 }} placeholder="e.g. auth.login_failed" value={action} onChange={(e) => { setAction(e.target.value.trim()); setPage(1); }} /></div>
      {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? <EmptyState emoji="📜" title="No events" /> : (<>
        <div className="table-wrap"><table>
          <thead><tr><th>When</th><th>Action</th><th>Actor</th><th>Entity</th><th>Detail</th></tr></thead>
          <tbody>{res.data.items.map((r) => <tr key={r.id}><td>{dateTime(r.created_at)}</td><td><code>{r.action}</code></td><td>{r.actor_id ? `#${r.actor_id}` : "—"}</td><td>{r.entity_type ? `${r.entity_type} #${r.entity_id}` : "—"}</td><td className="small muted">{r.detail ? JSON.stringify(r.detail) : ""}</td></tr>)}</tbody>
        </table></div>
        <Pager page={res.data} onPage={setPage} />
      </>)}
    </AdminShell>
  );
}
