"use client";
import Link from "next/link";
import { Icon, categoryIcon } from "@/components/Icon";
import { ProductCard } from "@/components/ProductCard";
import { useSession } from "@/components/Session";
import { api } from "@/lib/api";
import type { Category, Product, RecommendedProduct } from "@/lib/types";
import { useLoad } from "@/components/ui";

/** "Recommended for you" (signed-in buyers) or "Popular in Kabul" (everyone else). Renders nothing when there is nothing to show. */
export function Recommended({ limit = 4 }: { limit?: number }) {
  const { user } = useSession();
  const buyer = user?.role === "buyer";
  const rec = useLoad(() => api<RecommendedProduct[]>("recommendations", { query: { limit } }), [user?.id, limit]);
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const mine = useLoad(() => (buyer ? api<{ category_ids: number[] }>("me/interests") : Promise.resolve({ category_ids: [1] })), [buyer]);
  const name = new Map((cats.data ?? []).map((c) => [c.id, c.name]));
  if (!rec.data?.length) return null;
  const noInterests = buyer && mine.data && mine.data.category_ids.length === 0;
  return (
    <section className="section"><div className="wrap">
      <div className="row between"><h2>{buyer ? "Recommended for you" : "Popular in Kabul"}</h2>{buyer && <Link href="/interests"><Icon name="heart" size={14} /> My interests</Link>}</div>
      {noInterests && <p className="muted">Pick the categories you care about and we will tailor this list and tell you when something new arrives. <Link href="/interests">Choose interests</Link></p>}
      <div className="grid g4" style={{ marginTop: 20 }}>{rec.data.map((p: Product & { reason: string | null }) => <ProductCard key={p.id} p={p} icon={categoryIcon(name.get(p.category_id ?? -1))} why={buyer ? p.reason ?? undefined : undefined} />)}</div>
    </div></section>
  );
}

/** "You may also like" on a product page. */
export function Similar({ productId }: { productId: number }) {
  const sim = useLoad(() => api<Product[]>(`products/${productId}/similar`, { query: { limit: 4 } }), [productId]);
  const cats = useLoad(() => api<Category[]>("categories"), []);
  const name = new Map((cats.data ?? []).map((c) => [c.id, c.name]));
  if (!sim.data?.length) return null;
  return (
    <section style={{ marginTop: 56 }}>
      <h2>You may also like</h2>
      <div className="grid g4" style={{ marginTop: 20 }}>{sim.data.map((p) => <ProductCard key={p.id} p={p} icon={categoryIcon(name.get(p.category_id ?? -1))} />)}</div>
    </section>
  );
}
