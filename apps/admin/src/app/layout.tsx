import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Providers } from "@/lib/query";
import "./globals.css";

export const metadata: Metadata = { title: "DTM AI admin", robots: { index: false, follow: false } };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* eslint-disable-next-line @next/next/no-sync-scripts */}
        <script src="/env.js" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
