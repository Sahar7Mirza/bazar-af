"use client";
import { AdminShell } from "@/components/AdminShell";
import { ResearchView } from "@/components/ResearchView";

export default function Research() {
  return (
    <AdminShell title="Mobile money adoption">
      <p className="muted">Based on the payment preference buyers choose at checkout (cancelled orders excluded). This is the same analysis the public <a href="/research">Research page</a> shows, with every group visible and a data download for your paper.</p>
      <div style={{ height: 8 }} />
      <ResearchView admin />
    </AdminShell>
  );
}
