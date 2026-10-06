"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { EmptyState, LoadingRows } from "@/components/ui";
import { useSession } from "@/components/Session";
import { api } from "@/lib/api";

function Check() {
  const token = useSearchParams().get("token") ?? "";
  const { reload } = useSession();
  const [state, setState] = useState<"working" | "ok" | "bad">(token ? "working" : "bad");
  useEffect(() => {
    if (!token) return;
    let live = true;
    api("auth/verify-email", { method: "POST", body: { token } }).then(() => { if (live) { setState("ok"); reload(); } }).catch(() => live && setState("bad"));
    return () => { live = false; };
  }, [token, reload]);
  if (state === "working") return <LoadingRows n={2} />;
  if (state === "ok") return <EmptyState icon="check" title="Email confirmed" text="Thank you. Your email address is now verified." action={<Link className="btn" href="/products">Continue to Bazar.af</Link>} />;
  return <EmptyState icon="alert" title="This link is invalid or has expired" text="Sign in and use “Resend email” in the banner to get a new link." action={<Link className="btn" href="/login">Sign in</Link>} />;
}
export default function Verify() {
  return <div className="page"><div className="narrow"><Suspense><Check /></Suspense></div></div>;
}
