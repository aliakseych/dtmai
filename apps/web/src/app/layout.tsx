import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Providers } from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://dtm-ai.uz"),
  title: "DTM AI — DTM va litsey imtihonlariga tayyorgarlik",
  description: "Duolingo uslubida DTM tayyorgarligi: qisqa darslar, sinov imtihonlari va AI repetitor.",
  manifest: "/manifest.webmanifest",
  icons: { icon: [{ url: "/logo.svg", type: "image/svg+xml" }, { url: "/favicon.png", type: "image/png" }], apple: "/apple-touch-icon.png" },
  openGraph: { title: "DTM AI — DTM va litsey imtihonlariga tayyorgarlik", description: "Duolingo uslubida DTM tayyorgarligi: qisqa darslar, sinov imtihonlari va AI repetitor.", locale: "uz_UZ", siteName: "DTM AI", type: "website", images: [{ url: "/og.png", width: 1200, height: 630 }] },
  twitter: { card: "summary_large_image", title: "DTM AI — DTM va litsey imtihonlariga tayyorgarlik", description: "Duolingo uslubida DTM tayyorgarligi: qisqa darslar, sinov imtihonlari va AI repetitor.", images: ["/og.png"] },
};
export const viewport: Viewport = {
  themeColor: "#100FA0",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uz-Latn">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
