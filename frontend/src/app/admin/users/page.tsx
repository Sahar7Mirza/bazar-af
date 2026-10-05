"use client";
import { useState } from "react";
import { AdminShell } from "@/components/AdminShell";
import { useSession } from "@/components/Session";
import { Alert, EmptyState, ErrorState, LoadingRows, Pager, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { Page, User } from "@/lib/types";

export default function Users() {
  const { user: me } = useSession();
  const [page, setPage] = useState(1), [role, setRole] = useState(""), [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const res = useLoad(() => api<Page<User>>("admin/users", { query: { role, q, page, page_size: 10 } }), [role, q, page]);
  async function toggle(u: User) {
    setErr(null);
    try { await api(`admin/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } }); res.reload(); } catch (x) { setErr(x instanceof ApiError ? x.message : "Failed"); }
  }
  return (
    <AdminShell title="Users">
      <div className="row" style={{ marginBottom: 16 }}>
        <div><label className="sr" htmlFor="uq">Search users</label><input id="uq" type="search" placeholder="Name or email" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></div>
        <div><label className="sr" htmlFor="ur">Role</label><select id="ur" value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }}><option value="">All roles</option><option>buyer</option><option>seller</option><option>admin</option></select></div>
      </div>
      {err && <Alert kind="bad">{err}</Alert>}
      {res.loading ? <LoadingRows /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data?.items.length ? <EmptyState icon="users" title="No users match" /> : (<>
        <div className="table-wrap"><table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th><span className="sr">Actions</span></th></tr></thead>
          <tbody>{res.data.items.map((u) => <tr key={u.id}><td>{u.full_name}</td><td>{u.email}</td><td><span className="chip">{u.role}</span></td><td>{u.is_active ? <span className="chip ok">active</span> : <span className="chip bad">deactivated</span>}</td>
            <td style={{ textAlign: "right" }}><button className="btn quiet sm" disabled={u.id === me?.id} onClick={() => toggle(u)}>{u.is_active ? "Deactivate" : "Reactivate"}</button></td></tr>)}</tbody>
        </table></div>
        <Pager page={res.data} onPage={setPage} />
      </>)}
    </AdminShell>
  );
}
