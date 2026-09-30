"use client";
import { AdminShell } from "@/components/AdminShell";
import { OrderTable } from "@/components/Orders";

export default function AdminOrders() { return <AdminShell title="All orders"><OrderTable endpoint="admin/orders" showBuyer /></AdminShell>; }
