import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Footer, Nav } from "@/components/Nav";
import { LiveProvider, PendingBanner, VerifyBanner } from "@/components/Live";
import { SessionProvider } from "@/components/Session";

export const metadata: Metadata = {
  title: { default: "Bazar.af — Kabul’s marketplace for small businesses", template: "%s · Bazar.af" },
  description: "A marketplace for micro and small enterprises in Kabul, with a mobile-money adoption research study. No real payments are processed.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, colorScheme: "light dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <SessionProvider>
          <LiveProvider>
            <Nav />
            <VerifyBanner />
            <PendingBanner />
            <main id="main">{children}</main>
            <Footer />
          </LiveProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
