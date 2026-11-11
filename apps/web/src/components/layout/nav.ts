import type { MessageKey } from "@dtmai/i18n";

export type NavItem = { href: string; icon: string; label: MessageKey };

export const MAIN_NAV: NavItem[] = [
  { href: "/learn/", icon: "learn", label: "nav.learn" },
  { href: "/practice/", icon: "practice", label: "nav.practice" },
  { href: "/mocks/", icon: "mocks", label: "nav.mocks" },
  { href: "/leagues/", icon: "leagues", label: "nav.leagues" },
  { href: "/quests/", icon: "quests", label: "nav.quests" },
  { href: "/lyceums/", icon: "lyceums", label: "nav.lyceums" },
  { href: "/premium/", icon: "premium", label: "nav.premium" },
  { href: "/profile/", icon: "profile", label: "nav.profile" },
];

/** Bottom tab bar on mobile; everything else lives behind the "More" sheet. */
export const TAB_NAV = ["/learn/", "/practice/", "/mocks/", "/leagues/", "/profile/"];
export const MORE_NAV = MAIN_NAV.filter((n) => !TAB_NAV.includes(n.href));
