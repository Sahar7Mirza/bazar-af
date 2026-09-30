import { NextRequest, NextResponse } from "next/server";
import { AT, RT, clearAuthCookies, setAuthCookies } from "@/lib/cookies";
import { API_URL } from "@/lib/server";

// Token-handling endpoints are never proxied: login/logout have their own BFF routes, refresh happens only inside this handler.
const BLOCKED = new Set(["auth/login", "auth/refresh", "auth/logout"]);

async function call(path: string, req: NextRequest, body: string | undefined, token?: string) {
  const headers: Record<string, string> = {};
  const ct = req.headers.get("content-type");
  if (ct) headers["Content-Type"] = ct;
  if (token) headers.Authorization = `Bearer ${token}`;
  const rid = req.headers.get("x-request-id");
  if (rid) headers["X-Request-ID"] = rid;
  return fetch(`${API_URL}/${path}${req.nextUrl.search}`, { method: req.method, headers, body, cache: "no-store" });
}

async function handler(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const path = (await ctx.params).path.join("/");
  if (BLOCKED.has(path) || path.includes("..")) return NextResponse.json({ error: { code: "not_found", message: "Not found" } }, { status: 404 });
  if (req.method !== "GET") {  // CSRF defence in depth on top of SameSite=Lax
    const origin = req.headers.get("origin");
    if (origin && new URL(origin).host !== req.headers.get("host")) return NextResponse.json({ error: { code: "forbidden", message: "Cross-origin request blocked" } }, { status: 403 });
  }
  const body = ["GET", "HEAD"].includes(req.method) ? undefined : await req.text();
  let at = req.cookies.get(AT)?.value;
  const rt = req.cookies.get(RT)?.value;
  let refreshed: { access_token: string; refresh_token: string; expires_in: number } | null = null;
  let upstream = await call(path, req, body, at);
  if (upstream.status === 401 && rt) {
    const r = await fetch(`${API_URL}/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) });
    if (r.ok) {
      refreshed = await r.json();
      at = refreshed!.access_token;
      upstream = await call(path, req, body, at);
    }
  }
  const out = new NextResponse(upstream.status === 204 ? null : upstream.body, { status: upstream.status });
  for (const h of ["content-type", "content-disposition", "x-request-id"]) { const v = upstream.headers.get(h); if (v) out.headers.set(h, v); }
  if (refreshed) setAuthCookies(out, refreshed.access_token, refreshed.refresh_token, refreshed.expires_in);
  else if (upstream.status === 401 && rt) clearAuthCookies(out);
  return out;
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE };
