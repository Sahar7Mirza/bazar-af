"use client";
import { useSyncExternalStore } from "react";

export interface CartLine { productId: number; name: string; price: string; unit: string; sellerId: number; sellerName: string; qty: number; max: number }
const KEY = "bazar.cart.v1";
let cache: CartLine[] | null = null;
const listeners = new Set<() => void>();
const read = (): CartLine[] => {
  if (cache) return cache;
  try { cache = JSON.parse(localStorage.getItem(KEY) ?? "[]"); } catch { cache = []; }
  return cache!;
};
const write = (lines: CartLine[]) => {
  cache = lines;
  try { localStorage.setItem(KEY, JSON.stringify(lines)); } catch { /* storage unavailable: cart lives in memory only */ }
  listeners.forEach((l) => l());
};
const EMPTY: CartLine[] = [];

export const cart = {
  add(line: Omit<CartLine, "qty">, qty = 1) {
    const cur = read();
    if (cur.length && cur[0].sellerId !== line.sellerId) return { ok: false as const, reason: "one_seller" as const };
    const ex = cur.find((l) => l.productId === line.productId);
    const next = ex ? cur.map((l) => (l.productId === line.productId ? { ...l, qty: Math.min(l.max, l.qty + qty) } : l)) : [...cur, { ...line, qty: Math.min(line.max, qty) }];
    write(next);
    return { ok: true as const };
  },
  setQty(id: number, qty: number) { write(read().map((l) => (l.productId === id ? { ...l, qty: Math.max(1, Math.min(l.max, qty)) } : l))); },
  remove(id: number) { write(read().filter((l) => l.productId !== id)); },
  clear() { write([]); },
};
export function useCart(): CartLine[] {
  return useSyncExternalStore((cb) => { listeners.add(cb); return () => listeners.delete(cb); }, read, () => EMPTY);
}
export const cartTotal = (lines: CartLine[]) => lines.reduce((s, l) => s + Number(l.price) * l.qty, 0);
