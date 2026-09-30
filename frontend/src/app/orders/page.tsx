"use client";
import { OrderTable } from "@/components/Orders";
import { useSession } from "@/components/Session";
import { Guard } from "@/components/ui";

export default function Orders() {
  const { user, loading } = useSession();
  return <Guard roles={["buyer", "seller"]} user={user} loading={loading}><div className="wrap page"><h1 style={{ fontSize: "2.4rem" }}>{user?.role === "seller" ? "Incoming orders" : "My orders"}</h1><OrderTable showBuyer={user?.role === "seller"} /></div></Guard>;
}
