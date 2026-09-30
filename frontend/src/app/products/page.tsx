"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ProductCard } from "@/components/ProductCard";
import { EmptyState, ErrorState, LoadingGrid, Pager, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import { emojiFor } from "@/lib/emoji";
import { DISTRICTS, type Category, type Page, type Product } from "@/lib/types";

function Catalogue() {
  const router = useRouter();
  const sp = useSearchParams();
  const q = sp.get("q") ?? "", category_id = sp.get("category_id") ?? "", district = sp.get("district") ?? "", sort = sp.get("sort") ?? "created_at", order = sp.get("order") ?? "desc";
  const min_price = sp.get("min_price") ?? "", max_price = sp.get("max_price") ?? "", page = Number(sp.get("page") ?? 1);
  const set = (patch: Record<string, string>) => { const n = new URLSearchParams(sp.toString()); for (const [k, v] of Object.entries(patch)) v ? n.set(k, v) : n.delete(k); if (!("page" in patch)) n.delete("page"); router.push(`/products?${n}`); };
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const res = useLoad(() => api<Page<Product>>("products", { query: { q, category_id, district, sort, order, min_price, max_price, page, page_size: 12 } }), [q, category_id, district, sort, order, min_price, max_price, page]);
  const catName = new Map((cats.data ?? []).map((c) => [c.id, c.name]));
  const active = [q, category_id, district, min_price, max_price].some(Boolean);
  return (
    <div className="wrap page">
      <h1 style={{ fontSize: "2.4rem" }}>Shop</h1>
      <form role="search" className="row" style={{ marginBottom: 12 }} onSubmit={(e) => { e.preventDefault(); set({ q: String(new FormData(e.currentTarget).get("q") ?? "").trim() }); }}>
        <div className="grow" style={{ minWidth: 220 }}><label className="sr" htmlFor="q">Search products</label><input id="q" name="q" key={q} type="search" placeholder="Search bread, rugs, phone chargers…" defaultValue={q} /></div>
        <button className="btn">Search</button>
      </form>
      <div className="row" style={{ marginBottom: 24 }}>
        <div><label className="sr" htmlFor="cat">Category</label><select id="cat" value={category_id} onChange={(e) => set({ category_id: e.target.value })}><option value="">All categories</option>{(cats.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
        <div><label className="sr" htmlFor="dist">District</label><select id="dist" value={district} onChange={(e) => set({ district: e.target.value })}><option value="">All districts</option>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select></div>
        <div style={{ width: 110 }}><label className="sr" htmlFor="minp">Minimum price</label><input id="minp" inputMode="numeric" placeholder="Min AFN" defaultValue={min_price} onBlur={(e) => e.target.value !== min_price && set({ min_price: e.target.value.replace(/\D/g, "") })} /></div>
        <div style={{ width: 110 }}><label className="sr" htmlFor="maxp">Maximum price</label><input id="maxp" inputMode="numeric" placeholder="Max AFN" defaultValue={max_price} onBlur={(e) => e.target.value !== max_price && set({ max_price: e.target.value.replace(/\D/g, "") })} /></div>
        <div><label className="sr" htmlFor="sort">Sort</label><select id="sort" value={`${sort}:${order}`} onChange={(e) => { const [s, o] = e.target.value.split(":"); set({ sort: s, order: o }); }}>
          <option value="created_at:desc">Newest</option><option value="price:asc">Price: low to high</option><option value="price:desc">Price: high to low</option><option value="name:asc">Name A–Z</option></select></div>
        {active && <button className="link" onClick={() => router.push("/products")}>Clear filters</button>}
      </div>
      {res.loading ? <LoadingGrid n={8} /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !res.data || res.data.items.length === 0 ? (
        <EmptyState emoji="🔍" title="No products found" text={active ? "Try a different search or clear the filters." : "Nothing is listed yet."} action={active ? <button className="btn quiet" onClick={() => router.push("/products")}>Clear filters</button> : undefined} />
      ) : (<>
        <div className="grid g3">{res.data.items.map((p) => <ProductCard key={p.id} p={p} emoji={emojiFor(catName.get(p.category_id ?? -1))} />)}</div>
        <Pager page={res.data} onPage={(n) => set({ page: String(n) })} />
      </>)}
    </div>
  );
}
export default function Products() { return <Suspense><Catalogue /></Suspense>; }
