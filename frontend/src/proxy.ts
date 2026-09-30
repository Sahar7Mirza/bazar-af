import { NextRequest, NextResponse } from "next/server";

// Route guard (UX only - the API enforces RBAC on every call). Redirects obviously-unauthorised visits before any page code runs.
const RULES: { prefix: string; roles?: string[] }[] = [
  { prefix: "/admin", roles: ["admin"] },
  { prefix: "/seller", roles: ["seller"] },
  { prefix: "/orders", roles: ["buyer", "seller"] },
  { prefix: "/checkout", roles: ["buyer"] },
];

function roleOf(token?: string): string | null {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.role === "string" ? payload.role : null;
  } catch { return null; }
}

export function proxy(req: NextRequest) {
  const rule = RULES.find((r) => req.nextUrl.pathname === r.prefix || req.nextUrl.pathname.startsWith(r.prefix + "/"));
  if (!rule) return NextResponse.next();
  const at = req.cookies.get("baz_at")?.value;
  const rt = req.cookies.get("baz_rt")?.value;
  if (!at && !rt) {
    const url = new URL("/login", req.url);
    url.searchParams.set("next", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  const role = roleOf(at);
  if (role && rule.roles && !rule.roles.includes(role)) return NextResponse.redirect(new URL("/", req.url));
  return NextResponse.next();
}

export const config = { matcher: ["/admin/:path*", "/seller/:path*", "/orders/:path*", "/checkout/:path*"] };
