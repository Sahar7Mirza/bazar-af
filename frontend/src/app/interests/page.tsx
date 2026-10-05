"use client";
import { useState } from "react";
import { Icon, categoryIcon } from "@/components/Icon";
import { useSession } from "@/components/Session";
import { Alert, ErrorState, Guard, LoadingRows, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { Category } from "@/lib/types";

const MAX = 8;
export default function Interests() {
  const { user, loading } = useSession();
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const mine = useLoad(() => (user?.role === "buyer" ? api<{ category_ids: number[] }>("me/interests") : Promise.resolve({ category_ids: [] as number[] })), [user?.id]);
  const [edit, setEdit] = useState<number[] | null>(null);  // null = untouched, show what is saved
  const sel = edit ?? mine.data?.category_ids ?? [];
  const [msg, setMsg] = useState<{ kind: "ok" | "bad"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const toggle = (id: number) => { setMsg(null); setEdit(sel.includes(id) ? sel.filter((x) => x !== id) : sel.length < MAX ? [...sel, id] : sel); };
  async function save() {
    setBusy(true); setMsg(null);
    try { await api("me/interests", { method: "PUT", body: { category_ids: sel } }); setMsg({ kind: "ok", text: sel.length ? "Saved. Your recommendations are updated and you will be told when new products appear in these categories." : "Saved. You will only get order updates." }); }
    catch (e) { setMsg({ kind: "bad", text: e instanceof ApiError ? e.message : "Could not save. Try again." }); } finally { setBusy(false); }
  }
  return (
    <Guard roles={["buyer"]} user={user} loading={loading}>
      <div className="mid page">
        <h1 style={{ fontSize: "2.2rem" }}>My interests</h1>
        <p className="muted">Choose what you like to buy. We use this to recommend products and to notify you when a seller lists something new in these categories.</p>
        {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
        {cats.loading || mine.loading ? <LoadingRows n={4} /> : cats.error ? <ErrorState error={cats.error} retry={cats.reload} /> : (<>
          <div className="grid g2" role="group" aria-label="Categories you are interested in">
            {(cats.data ?? []).map((c) => {
              const on = sel.includes(c.id);
              return (
                <button key={c.id} type="button" className={`card hover interest ${on ? "on" : ""}`} aria-pressed={on} onClick={() => toggle(c.id)}>
                  <span className="cat-icon"><Icon name={categoryIcon(c.name)} size={26} /></span>
                  <strong>{c.name}</strong>
                  {on && <Icon name="check" size={20} className="tick" />}
                </button>
              );
            })}
          </div>
          <div className="row" style={{ marginTop: 24 }}><button className="btn lg" disabled={busy} onClick={save}>{busy ? "Saving…" : "Save interests"}</button><span className="muted small">{sel.length} of {MAX} selected</span></div>
        </>)}
      </div>
    </Guard>
  );
}
