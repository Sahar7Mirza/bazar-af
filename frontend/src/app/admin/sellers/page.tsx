"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AdminShell } from "@/components/AdminShell";
import { Alert, EmptyState, ErrorState, LoadingRows, Pager, StatusChip, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { date } from "@/lib/format";
import type { Page, Seller } from "@/lib/types";

function Sellers() {
  const router = useRouter();
  const status = useSearchParams().get("status") ?? "";
  const [page, setPage] = useState(1);
  const [err, setErr] = useState<string | null>(null);
  const res = useLoad(() => api<Page<Seller>>("admin/sellers", { query: { status, page, page_size: 10 } }), [status, page]);
  async function act(id: number, what: "approve" | "reject" | "suspend") {
    const note = what === "approve" ? null : window.prompt(`Note for the seller (${what}):`) ;
    if (what !== "approve" && note === null) return;
    setErr(null);
    try { await api(`admin/sellers/${id}/${what}`, { method: "POST", body: { note } }); res.reload(); } catch (x) { setErr(x instanceof ApiError ? x.message : "Failed"); }
  }
  return (
    <AdminShell title="Sellers">
      <div className="row" style={{ marginBottom: 16 }}><label className="sr" htmlFor="st">Status</label>
        <select id="st" style={{ width: "auto" }} value={status} onChange={(e) => { setPage(1); router.push(e.target.value ? `/admin/sellers?status=${e.target.value}` : "/admin/sellers"); }}>
          <option value="">All</option>{["pending", "approved", "rejected", "suspended"].map((s) => <option key={s}>{s}</option>)}</select></div>
      {err && <Alert kind="bad">{err}</Alert>}
      {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? <EmptyState icon="store" title="No sellers here" /> : (<>
        <div className="table-wrap"><table>
          <thead><tr><th>Business</th><th>District</th><th>Registered</th><th>Status</th><th><span className="sr">Actions</span></th></tr></thead>
          <tbody>{res.data.items.map((s) => (
            <tr key={s.id}><td><strong>{s.business_name}</strong><div className="muted small">{s.phone}</div></td><td>{s.district ?? "—"}</td><td>{date(s.created_at)}</td><td><StatusChip status={s.status} /></td>
              <td><div className="row" style={{ justifyContent: "flex-end" }}>
                {s.status !== "approved" && <button className="btn sm" onClick={() => act(s.id, "approve")}>Approve</button>}
                {s.status === "pending" && <button className="btn quiet sm" onClick={() => act(s.id, "reject")}>Reject</button>}
                {s.status === "approved" && <button className="btn quiet sm" onClick={() => act(s.id, "suspend")}>Suspend</button>}</div></td></tr>))}</tbody>
        </table></div>
        <Pager page={res.data} onPage={setPage} />
      </>)}
    </AdminShell>
  );
}
export default function Page() { return <Suspense><Sellers /></Suspense>; }
