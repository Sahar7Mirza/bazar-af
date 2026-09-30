"use client";
import { OrderTable } from "@/components/Orders";
import { SellerShell } from "@/components/SellerShell";

export default function SellerOrders() { return <SellerShell title="Orders"><OrderTable showBuyer /></SellerShell>; }
