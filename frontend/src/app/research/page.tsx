import type { Metadata } from "next";
import Link from "next/link";
import { ResearchView } from "@/components/ResearchView";

export const metadata: Metadata = { title: "Research: how Kabul shoppers choose to pay", description: "Open, anonymous figures on how many Bazar.af orders choose Mobile Money instead of Cash." };

export default function PublicResearch() {
  return (
    <div className="wrap page">
      <p className="eyebrow">Open research</p>
      <h1 style={{ fontSize: "clamp(2rem, 5vw, 3rem)" }}>How do Kabul shoppers choose to pay?</h1>
      <p className="lead muted" style={{ maxWidth: 720 }}>Every time someone checks out on Bazar.af they pick Cash or Mobile Money. We count those choices, openly and anonymously, to show how ready small shops and their customers are for mobile money. Sellers can use it to decide whether to offer it; researchers can use it as evidence.</p>
      <p className="small"><Link href="/products">Browse the marketplace</Link> to add your own choice to the picture.</p>
      <div style={{ height: 16 }} />
      <ResearchView />
    </div>
  );
}
