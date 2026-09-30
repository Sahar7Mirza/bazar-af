"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useCart } from "@/lib/cart";
import { useSession } from "./Session";

export function Nav() {
  const { user, loading, logout } = useSession();
  const path = usePathname();
  const cart = useCart();
  const [open, setOpen] = useState(false);
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
