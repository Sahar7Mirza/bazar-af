"use client";
import { Icon } from "@/components/Icon";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { ApiError } from "@/lib/api";
import type { OrderStatus, Page } from "@/lib/types";

export function Skeleton({ h = 20, w = "100%" }: { h?: number; w?: string | number }) { return <div className="skeleton" style={{ height: h, width: w }} aria-hidden="true" />; }
export function LoadingGrid({ n = 6, h = 220 }: { n?: number; h?: number }) {
  return <div className="grid g3" role="status" aria-label="Loading">{Array.from({ length: n }, (_, i) => <div key={i} className="card"><Skeleton h={h} /></div>)}<span className="sr">Loading…</span></div>;
}
export function LoadingRows({ n = 5 }: { n?: number }) { return <div role="status" aria-label="Loading" className="stack">{Array.from({ length: n }, (_, i) => <Skeleton key={i} h={44} />)}<span className="sr">Loading…</span></div>; }
export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  const e = error instanceof ApiError ? error : null;
  return (
    <div className="state" role="alert">
      <div className="state-icon"><Icon name="alert" size={36} /></div><h3>{e?.status === 403 ? "You don’t have access to this" : "Something went wrong"}</h3>
      <p>{e?.message ?? "Please try again."}</p>{e?.requestId && <p className="small">Reference: {e.requestId}</p>}
      {retry && <button className="btn quiet" onClick={retry}>Try again</button>}
    </div>
  );
}
export function EmptyState({ title, text, action, icon = "folder" }: { title: string; text?: string; action?: ReactNode; icon?: string }) {
  return <div className="state"><div className="state-icon"><Icon name={icon} size={36} /></div><h3>{title}</h3>{text && <p>{text}</p>}{action}</div>;
}
export function Alert({ kind = "info", children }: { kind?: "bad" | "ok" | "info" | "warn"; children: ReactNode }) { return <div className={`alert ${kind}`} role={kind === "bad" ? "alert" : "status"}>{children}</div>; }

export function Pager<T>({ page, onPage }: { page: Page<T>; onPage: (p: number) => void }) {
  if (page.pages <= 1) return <p className="pager">{page.total} result{page.total === 1 ? "" : "s"}</p>;
  return (
    <nav className="pager" aria-label="Pagination">
      <button className="btn quiet sm" disabled={page.page <= 1} onClick={() => onPage(page.page - 1)}>← Previous</button>
      <span>Page {page.page} of {page.pages} · {page.total} results</span>
      <button className="btn quiet sm" disabled={page.page >= page.pages} onClick={() => onPage(page.page + 1)}>Next →</button>
    </nav>
  );
}

const STATUS_KIND: Record<string, string> = { pending: "warn", confirmed: "info", ready: "info", completed: "ok", cancelled: "bad", approved: "ok", rejected: "bad", suspended: "bad", active: "ok", hidden: "" };
export function StatusChip({ status }: { status: OrderStatus | string }) { return <span className={`chip ${STATUS_KIND[status] ?? ""}`}>{status}</span>; }

/** Data loader with the four states every view needs: loading, error, empty (caller decides) and content. Re-runs when `deps` change. */
export function useLoad<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [tick, setTick] = useState(0);
  const key = `${JSON.stringify(deps)}#${tick}`;
  const [res, setRes] = useState<{ key: string; data?: T; error?: unknown }>();
  useEffect(() => {
    let live = true;
    loader().then((data) => live && setRes({ key, data })).catch((error) => live && setRes({ key, error }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const fresh = res?.key === key;  // stale results are hidden while the next request is in flight
  // refresh() swaps in new data quietly (no loading flash); used by live updates. reload() shows the loading state.
  const refresh = () => { loader().then((data) => setRes({ key, data })).catch(() => {}); };
  return { data: fresh ? res.data : undefined, error: fresh ? res.error : undefined, loading: !fresh, reload: () => setTick((t) => t + 1), refresh };
}

export function Field({ label, error, hint, children, id }: { label: string; error?: string; hint?: string; children: ReactNode; id: string }) {
  return <div className="field"><label htmlFor={id}>{label}</label>{children}{hint && !error && <div className="hint">{hint}</div>}{error && <div className="err" id={`${id}-err`} role="alert">{error}</div>}</div>;
}

export function TabNav({ items, current }: { items: [string, string][]; current: string }) {
  return <nav className="tabs" aria-label="Section">{items.map(([href, label]) => <Link key={href} href={href} aria-current={current === href ? "page" : undefined}>{label}</Link>)}</nav>;
}

export function Guard({ roles, user, loading, children, denied }: { roles: string[]; user: { role: string } | null; loading: boolean; children: ReactNode; denied?: string }) {
  if (loading) return <div className="wrap page"><LoadingRows /></div>;
  if (!user) return <div className="wrap page"><EmptyState icon="lock" title="Please sign in" text="You need an account to see this page." action={<Link className="btn" href="/login">Sign in</Link>} /></div>;
  if (!roles.includes(user.role)) return <div className="wrap page"><EmptyState icon="ban" title="Not available for your account type" text={denied} action={<Link className="btn quiet" href="/">Back home</Link>} /></div>;
  return <>{children}</>;
}
