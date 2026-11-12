import type { NextConfig } from "next";

const config: NextConfig = {
  // Static export for builds only: `next dev` with export rejects lesson ids outside generateStaticParams.
  output: process.env.NODE_ENV === "production" ? "export" : undefined,
  trailingSlash: true,
  images: { unoptimized: true },
  transpilePackages: ["@dtmai/ui", "@dtmai/i18n", "@dtmai/api-client"],
};

export default config;
