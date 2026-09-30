"use client";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useSession } from "@/components/Session";
import { Alert, Guard, TabNav, useLoad } from "@/components/ui";
import { api } from "@/lib/api";
import type { Seller } from "@/lib/types";

export function SellerShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, loading } = useSession();
  const path = usePathname();
  const me = useLoad(() => api<Seller>("sellers/me"), [user?.id]);
  const tab = path.startsWith("/seller/products") ? "/seller/products" : path;
  return (
    <Guard roles={["seller"]} user={user} loading={loading}>
      <div className="wrap page">
        <div className="row between"><h1 style={{ fontSize: "2.4rem" }}>{title}</h1></div>
        <TabNav current={tab} items={[["/seller", "Overview"], ["/seller/products", "Products"], ["/seller/orders", "Orders"], ["/seller/profile", "Shop profile"]]} />
        <div style={{ height: 24 }} />
        {me.data && me.data.status !== "approved" && <Alert kind={me.data.status === "pending" ? "warn" : "bad"}>{me.data.status === "pending" ? "Your shop is waiting for administrator approval. You can prepare your profile now; products go live after approval." : `Your shop is ${me.data.status}.${me.data.review_note ? ` Note: ${me.data.review_note}` : ""}`}</Alert>}
        {children}
      </div>
    </Guard>
  );
}
