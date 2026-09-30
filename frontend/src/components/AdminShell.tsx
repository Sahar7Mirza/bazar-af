"use client";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useSession } from "@/components/Session";
import { Guard, TabNav } from "@/components/ui";

export function AdminShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, loading } = useSession();
  const path = usePathname();
  return (
    <Guard roles={["admin"]} user={user} loading={loading}>
      <div className="wrap page">
        <h1 style={{ fontSize: "2.4rem" }}>{title}</h1>
        <TabNav current={path} items={[["/admin", "Overview"], ["/admin/sellers", "Sellers"], ["/admin/users", "Users"], ["/admin/orders", "Orders"], ["/admin/research", "Research"], ["/admin/audit", "Audit log"]]} />
        <div style={{ height: 24 }} />
        {children}
      </div>
    </Guard>
  );
}
