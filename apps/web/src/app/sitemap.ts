import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://dtm-ai.uz";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["/", "/login/", "/register/"].map((path) => ({ url: `${SITE}${path}` }));
}
