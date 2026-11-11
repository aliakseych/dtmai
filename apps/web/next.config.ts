import type { NextConfig } from "next";

const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  transpilePackages: ["@dtmai/ui", "@dtmai/i18n", "@dtmai/api-client"],
};

export default config;
