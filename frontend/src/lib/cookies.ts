import "server-only";
import type { NextResponse } from "next/server";

export const AT = "baz_at";
export const RT = "baz_rt";
const secure = process.env.NODE_ENV === "production" && process.env.COOKIE_SECURE !== "false";

export function setAuthCookies(res: NextResponse, access: string, refresh: string, expiresIn: number, refreshDays = 7) {
  res.cookies.set(AT, access, { httpOnly: true, sameSite: "lax", secure, path: "/", maxAge: expiresIn });
  res.cookies.set(RT, refresh, { httpOnly: true, sameSite: "lax", secure, path: "/api", maxAge: refreshDays * 86400 });
}
export function clearAuthCookies(res: NextResponse) {
  res.cookies.set(AT, "", { path: "/", maxAge: 0 });
  res.cookies.set(RT, "", { path: "/api", maxAge: 0 });
}
