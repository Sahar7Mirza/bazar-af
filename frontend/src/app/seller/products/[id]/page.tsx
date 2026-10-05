"use client";
import { useParams } from "next/navigation";
import { ProductForm } from "@/components/ProductForm";
import { SellerShell } from "@/components/SellerShell";
import { EmptyState, ErrorState, LoadingRows, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import type { Page, Product } from "@/lib/types";

export default function EditProduct() {
  const { id } = useParams<{ id: string }>();
  const res = useLoad(() => api<Page<Product>>("sellers/me/products", { query: { page_size: 100 } }), []);
  const p = res.data?.items.find((x) => String(x.id) === id);
  return (
    <SellerShell title="Edit product">
      {res.loading ? <LoadingRows n={4} /> : res.error ? <ErrorState error={res.error} retry={res.reload} /> : !p ? <EmptyState icon="search" title="Product not found" /> : <ProductForm product={p} />}
    </SellerShell>
  );
}
