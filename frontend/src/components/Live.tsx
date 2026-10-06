"use client";
import Link from "next/link";
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import { Icon } from "./Icon";
import { useSession } from "./Session";
import type { LiveState } from "@/lib/types";

const POLL_MS = 5000; // how often the app asks "anything new?" while the tab is open
const EMPTY: LiveState = { unread: 0, latest: null };
interface Ctx { live: LiveState; version: number; refresh: () => void }
const LiveCtx = createContext<Ctx>({ live: EMPTY, version: 0, refresh: () => {} });
export const useLive = () => useContext(LiveCtx);

/** Re-runs `fn` (a silent data refresh) whenever the live state changes, so lists update without a page reload. */
export function useLiveRefresh(fn: () => void) {
  const { version } = useLive();
  const first = useRef(version);
  const latest = useRef(fn);
  useEffect(() => { latest.current = fn; });
  useEffect(() => { if (version !== first.current) latest.current(); }, [version]);
}

/**
 * Keeps one lightweight request going (unread count, newest alert, and for sellers the orders still waiting).
 * Polling stops while the tab is hidden and fires immediately when the person comes back to it.
 */
export function LiveProvider({ children }: { children: ReactNode }) {
  const { user } = useSession();
  const uid = user?.id;
  const [polled, setLive] = useState<LiveState>(EMPTY);
  const live = uid ? polled : EMPTY;  // signed out -> nothing to show, without resetting state inside an effect
  const [version, setVersion] = useState(0);
  const [toastRaw, setToast] = useState<LiveState["latest"]>(null);
  const toast = uid ? toastRaw : null;
  const seen = useRef<number | null>(null);
  const prev = useRef<string>("");
  const pull = useRef<() => void>(() => {});

  useEffect(() => {
    seen.current = null; prev.current = "";
    if (!uid) return;
    let alive = true;
    const load = () => {
      if (document.hidden) return;
      api<LiveState>("notifications/unread-count").then((r) => {
        if (!alive) return;
        setLive(r);
        const sig = `${r.unread}|${r.latest?.id ?? 0}|${r.pending_orders ?? 0}`;
        if (prev.current && sig !== prev.current) setVersion((v) => v + 1);
        prev.current = sig;
        const newest = r.latest?.id ?? 0;
        if (r.latest && seen.current !== null && newest > seen.current) setToast(r.latest);  // a brand-new alert arrived while the app was open
        if (seen.current === null || newest > seen.current) seen.current = newest;
      }).catch(() => {});
    };
    pull.current = load;
    load();
    const t = setInterval(load, POLL_MS);
    const wake = () => { if (!document.hidden) load(); };
    document.addEventListener("visibilitychange", wake);
    window.addEventListener("focus", wake);
    return () => { alive = false; clearInterval(t); document.removeEventListener("visibilitychange", wake); window.removeEventListener("focus", wake); };
  }, [uid]);

  useEffect(() => {  // "(2) Bazar.af" in the browser tab so a waiting order is noticed even from another tab
    const n = user?.role === "seller" ? (live.pending_orders ?? 0) : live.unread;
    const base = document.title.replace(/^\(\d+\)\s*/, "");
    document.title = n > 0 ? `(${n}) ${base}` : base;
  }, [live, user?.role]);

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(null), 9000); return () => clearTimeout(t); }, [toast]);

  return (
    <LiveCtx.Provider value={{ live, version, refresh: () => pull.current() }}>
      {children}
      {toast && (
        <div className="toast" role="status" aria-live="polite">
          <Icon name={toast.kind === "new_order" ? "bag" : "bell-ring"} size={18} />
          <div><strong>{toast.title}</strong><span>{toast.message}</span></div>
          <Link className="btn sm" href={toast.order_id ? `/orders/${toast.order_id}` : "/notifications"} onClick={() => setToast(null)}>{toast.kind === "new_order" ? "Review" : "View"}</Link>
          <button className="link" aria-label="Dismiss" onClick={() => setToast(null)}><Icon name="x" size={16} /></button>
        </div>
      )}
    </LiveCtx.Provider>
  );
}

/** Sits under the top bar on every page until the seller has confirmed or cancelled every waiting order. */
export function PendingBanner() {
  const { user } = useSession();
  const n = useLive().live.pending_orders ?? 0;
  if (user?.role !== "seller" || n === 0) return null;
  return (
    <div className="waiting" role="status">
      <Icon name="bell-ring" size={16} />
      <span><strong>{n} new order{n === 1 ? "" : "s"}</strong> waiting for you. Confirm or cancel {n === 1 ? "it" : "them"} so the buyer knows what is happening.</span>
      <Link className="btn sm" href="/seller/orders">Review now</Link>
    </div>
  );
}
