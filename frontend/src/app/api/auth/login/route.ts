import { NextRequest, NextResponse } from "next/server";
import { setAuthCookies } from "@/lib/cookies";
import { API_URL } from "@/lib/server";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const res = await fetch(`${API_URL}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json", "X-Forwarded-For": req.headers.get("x-forwarded-for") ?? "" }, body });
  const data = await res.json().catch(() => null);
  if (!res.ok) return NextResponse.json(data ?? { error: { code: "error", message: "Login failed" } }, { status: res.status });
  const out = NextResponse.json({ user: data.user });  // tokens never reach browser JavaScript
  setAuthCookies(out, data.access_token, data.refresh_token, data.expires_in);
  return out;
}
