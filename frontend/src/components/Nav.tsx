"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { useSession } from "./Session";

export function Nav() {
  const { user, loading, logout } = useSession();
  const path = usePathname();
  const cart = useCart();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const uid = user?.id;
  useEffect(() => {  // poll the unread count every 30 s (and whenever the page changes) so a "confirmed / ready" alert shows up on its own
    if (!uid) return;
    let live = true;
    const load = () => api<{ unread: number }>("notifications/unread-count").then((r) => live && setUnread(r.unread)).catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => { live = false; clearInterval(t); };
  }, [uid, path]);
  const n = cart.reduce((s, l) => s + l.qty, 0);
  const cur = (href: string) => (path === href || (href !== "/" && path.startsWith(href)) ? "page" : undefined);
  const home = user?.role === "admin" ? "/admin" : user?.role === "seller" ? "/seller" : null;
  return (
    <header className="top">
      <div className="top-in">
        <Link href="/" className="brand">Bazar.af</Link>
        <button className="btn quiet sm menu-btn" aria-expanded={open} aria-controls="mainnav" onClick={() => setOpen(!open)}>{open ? "Close" : "Menu"}</button>
        <nav id="mainnav" className={`nav ${open ? "open" : ""}`} aria-label="Main" onClick={() => setOpen(false)}>
          <Link href="/products" aria-current={cur("/products")}>Shop</Link>
          <Link href="/survey" aria-current={cur("/survey")}>Research survey</Link>
          {user && user.role !== "admin" && <Link href="/orders" aria-current={cur("/orders")}>Orders</Link>}
          {home && <Link href={home} aria-current={cur(home)}>{user?.role === "admin" ? "Admin" : "My shop"}</Link>}
        </nav>
        <div className="nav-right">
          {(!user || user.role === "buyer") && <Link href="/cart" aria-label={`Cart, ${n} items`}>Cart{n > 0 ? ` (${n})` : ""}</Link>}
          {user && <Link href="/notifications" className="bell" aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}>🔔{unread > 0 && uid && <span className="dot">{unread > 9 ? "9+" : unread}</span>}</Link>}
          {loading ? null : user ? (<><span className="muted small">{user.full_name.split(" ")[0]}</span><button className="link" onClick={logout}>Sign out</button></>) : (<><Link href="/login">Sign in</Link><Link href="/register" className="btn sm">Join</Link></>)}
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="foot"><div className="wrap">
      <p>Bazar.af is a capstone research project for micro and small enterprises in Kabul. <strong>No real payments are processed</strong> — the platform only records a simulated Cash or Mobile Money preference.</p>
      <p>Bachelor of Computer Science capstone · Demo data is synthetic.</p>
    </div></footer>
  );
}
