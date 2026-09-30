"use client";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

interface Ctx { user: User | null; loading: boolean; reload: () => Promise<void>; logout: () => Promise<void>; setUser: (u: User | null) => void }
const SessionCtx = createContext<Ctx>({ user: null, loading: true, reload: async () => {}, logout: async () => {}, setUser: () => {} });
export const useSession = () => useContext(SessionCtx);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const reload = useCallback(async () => {
    try { setUser(await api<User>("auth/me")); } catch { setUser(null); } finally { setLoading(false); }
  }, []);
  useEffect(() => {
    let live = true;
    api<User>("auth/me").then((u) => live && setUser(u)).catch(() => live && setUser(null)).finally(() => live && setLoading(false));
    return () => { live = false; };
  }, []);
  const logout = useCallback(async () => { await fetch("/api/auth/logout", { method: "POST" }); setUser(null); router.push("/"); router.refresh(); }, [router]);
  return <SessionCtx.Provider value={{ user, loading, reload, logout, setUser }}>{children}</SessionCtx.Provider>;
}
