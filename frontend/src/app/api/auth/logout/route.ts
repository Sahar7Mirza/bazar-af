import { NextRequest, NextResponse } from "next/server";
import { RT, clearAuthCookies } from "@/lib/cookies";
import { API_URL } from "@/lib/server";

export async function POST(req: NextRequest) {
  const rt = req.cookies.get(RT)?.value;
  if (rt) await fetch(`${API_URL}/auth/logout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) }).catch(() => null);
  const out = new NextResponse(null, { status: 204 });
  clearAuthCookies(out);
  return out;
}
