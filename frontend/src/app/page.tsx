import Link from "next/link";
import { ProductCard } from "@/components/ProductCard";
import { Icon, categoryIcon } from "@/components/Icon";
import { Recommended } from "@/components/Recommended";
import { publicGet } from "@/lib/server";
import type { Category, Page, Product } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [products, cats] = await Promise.all([publicGet<Page<Product>>("products?page_size=8"), publicGet<Category[]>("categories")]);
  const catName = new Map((cats ?? []).map((c) => [c.id, c.name]));
  return (
    <>
      <section className="hero wrap">
        <p className="eyebrow">Bazar.af</p>
        <h1>Kabul’s small businesses,<br />one marketplace.</h1>
        <p className="lead">Discover local bakeries, tailors, grocers and workshops. Order in a few taps and tell the seller how you’d like to pay — cash or mobile money.</p>
        <div className="row center"><Link className="btn lg" href="/products">Start shopping</Link><Link className="btn lg ghost" href="/register">Sell on Bazar.af</Link></div>
        <p className="muted small" style={{ marginTop: 18 }}>No real payments are processed. Your choice is recorded as a preference only.</p>
      </section>

      <section className="section alt"><div className="wrap">
        <h2 className="center">Browse by category</h2>
        <div className="grid g4" style={{ marginTop: 28 }}>
          {(cats ?? []).map((c) => (
            <Link key={c.id} href={`/products?category_id=${c.id}`} className="card hover center" style={{ color: "inherit" }}>
              <div className="cat-icon"><Icon name={categoryIcon(c.name)} size={30} /></div><strong>{c.name}</strong>
            </Link>
          ))}
        </div>
      </div></section>

      <Recommended />

      <section className="section alt"><div className="wrap">
        <div className="row between"><h2>Fresh on the market</h2><Link href="/products">See all →</Link></div>
        {products && products.items.length > 0 ? (
          <div className="grid g3" style={{ marginTop: 20 }}>{products.items.map((p) => <ProductCard key={p.id} p={p} icon={categoryIcon(catName.get(p.category_id ?? -1))} />)}</div>
        ) : (
          <div className="state"><h3>The market is warming up</h3><p>No products to show yet. Check back soon.</p></div>
        )}
      </div></section>

      <section className="section alt"><div className="wrap">
        <h2 className="center">How it works</h2>
        <div className="grid g3" style={{ marginTop: 28 }}>
          {[["1", "Browse", "Search and filter products from approved local sellers."], ["2", "Order", "Add items from one seller and choose Cash or Mobile Money."], ["3", "Pick up", "The seller confirms, prepares and completes your order."]].map(([n, t, d]) => (
            <div key={n} className="card"><div className="eyebrow">Step {n}</div><h3>{t}</h3><p className="muted">{d}</p></div>
          ))}
        </div>
      </div></section>

      <section className="section"><div className="mid center">
        <h2>Cash or Mobile Money, your choice</h2>
        <p className="lead muted">At checkout you tell the seller how you plan to pay. No money moves on Bazar.af, and your choice helps show how many people in Kabul use mobile money.</p>
        <Link className="btn lg" href="/products">Start shopping</Link>
      </div></section>
    </>
  );
}
