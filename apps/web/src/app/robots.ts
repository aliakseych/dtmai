import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://dtm-ai.uz";

export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: ["/", "/login/", "/register/"], disallow: ["/learn/", "/practice/", "/mocks/", "/profile/", "/leagues/", "/lyceum/", "/lyceums/", "/rep/", "/settings/", "/premium/", "/quests/", "/onboarding/"] }, sitemap: `${SITE}/sitemap.xml` };
}
