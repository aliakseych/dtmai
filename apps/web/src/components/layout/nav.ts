import type { MessageKey } from "@dtmai/i18n";
import type { IconName } from "@dtmai/ui";

export type NavItem = { href: string; icon: IconName; label: MessageKey };

export const MAIN_NAV: NavItem[] = [
  { href: "/home/", icon: "home", label: "nav.home" },
  { href: "/learn/", icon: "learn", label: "nav.learn" },
  { href: "/plan/", icon: "plan", label: "nav.plan" },
  { href: "/exam/", icon: "exam", label: "nav.exam" },
  { href: "/practice/", icon: "practice", label: "nav.practice" },
  { href: "/mocks/", icon: "mocks", label: "nav.mocks" },
  { href: "/leagues/", icon: "leagues", label: "nav.leagues" },
  { href: "/quests/", icon: "quests", label: "nav.quests" },
  { href: "/lyceums/", icon: "lyceums", label: "nav.lyceums" },
  { href: "/premium/", icon: "premium", label: "nav.premium" },
  { href: "/temur/", icon: "temur", label: "nav.temur" },
  { href: "/rep/", icon: "rep", label: "nav.rep" },
  { href: "/profile/", icon: "profile", label: "nav.profile" },
];

/** Bottom tab bar on mobile; everything else lives behind the "More" sheet. */
export const TAB_NAV = ["/home/", "/learn/", "/plan/", "/mocks/"];
export const MORE_NAV = MAIN_NAV.filter((n) => !TAB_NAV.includes(n.href));
