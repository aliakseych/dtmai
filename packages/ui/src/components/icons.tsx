import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;
const base = { viewBox: "0 0 24 24", width: 24, height: 24, "aria-hidden": true } as const;

/** Line icons: 24 grid, 2px round stroke, no fill, `currentColor`. One path string per icon. */
const LINE = {
  home: "M3 11.5 12 4l9 7.5M5 10v10h5v-6h4v6h5V10",
  learn: "M12 6.5C10.5 5 8 4.5 3 4.5v14c5 0 7.5.5 9 2 1.5-1.5 4-2 9-2v-14c-5 0-7.5.5-9 2zM12 6.5v14",
  plan: "M4 6h16a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zM8 3v5M16 3v5M3 11h18",
  exam: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 12v.01",
  practice: "M4 20l4-1L20 7a2.1 2.1 0 0 0-3-3L5 16zM14.5 6.5l3 3",
  mocks: "M6 3h8l5 5v13H6zM14 3v5h5M9 13h6M9 17h4",
  leagues: "M8 4h8v5a4 4 0 0 1-8 0zM8 5H4v1a4 4 0 0 0 4 4M16 5h4v1a4 4 0 0 1-4 4M12 13v4M9 21v-4h6v4M7 21h10",
  quests: "M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM8 12l3 3 5-6",
  profile: "M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9zM4 21a8 8 0 0 1 16 0",
  premium: "M3 8l4 4 5-8 5 8 4-4-2 12H5z",
  more: "M5 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM12 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2zM19 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2z",
  lyceums: "M2 9l10-5 10 5-10 5zM6 11.5V16c0 1.5 3 3 6 3s6-1.5 6-3v-4.5M22 9v6",
  temur: "M5 4h14a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-9l-5 4v-4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM8 8.5h8M8 12h5",
  rep: "M4 7h16a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1zM9 7V4h6v3M3 13h18",
  "chevron-left": "m15 6-6 6 6 6",
  "chevron-right": "m9 6 6 6-6 6",
  "chevron-up": "m6 15 6-6 6 6",
  "chevron-down": "m6 9 6 6 6-6",
  "arrow-left": "M19 12H5M11 6l-6 6 6 6",
  "arrow-up": "M12 19V5M6 11l6-6 6 6",
  "arrow-down": "M12 5v14M6 13l6 6 6-6",
  close: "M6 6l12 12M18 6 6 18",
  check: "m5 12.5 4.5 4.5L19 7",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  menu: "M4 7h16M4 12h16M4 17h16",
  lock: "M6 11h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1zM8 11V7a4 4 0 0 1 8 0v4",
  flag: "M5 21V4h12l-2 4 2 4H5",
  alert: "M12 3 2 20h20zM12 10v4M12 17v.01",
  snowflake: "M12 2v20M3.3 7l17.4 10M20.7 7 3.3 17M9 4l3 3 3-3M9 20l3-3 3 3",
  bolt: "M13 2 4 14h6l-1 8 9-12h-6z",
  review: "M20 11a8 8 0 0 0-14.5-4M4 4v4h4M4 13a8 8 0 0 0 14.5 4M20 20v-4h-4",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2",
  help: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 17v.01M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.7",
  heart: "M12 20s-8-5-8-10.5A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 8 2.5C20 15 12 20 12 20z",
} as const;

export type IconName = keyof typeof LINE;
/** sm 16 (inside text/badges) · md 20 (buttons, rows) · lg 24 (default, tab bar) · xl 28 (sidebar, icon tiles) · 32 (empty states). */
export type IconSize = 16 | 20 | 24 | 28 | 32;

/** The only way to draw a UI icon. Decorative by default; pass `label` when the icon is the sole content. */
export function Icon({ name, size = 24, label, className }: { name: IconName; size?: IconSize; label?: string; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className={className ? `shrink-0 ${className}` : "shrink-0"}
    >
      <path d={LINE[name]} />
    </svg>
  );
}

/* Status glyphs: filled, token-coloured. Only for stats, path nodes and answer feedback. */
export const FlameIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-4 2-7 1 1 2 2 2.5 3C11 8 11 5 12 2z" fill="var(--color-brand)" />
    <path d="M12 12c1 2 3 2.5 3 5a3 3 0 0 1-6 0c0-2 2-2.5 3-5z" fill="var(--color-accent)" />
  </svg>
);
export const HeartIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z" fill="var(--color-red)" />
  </svg>
);
export const GemIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M6 3h12l4 6-10 12L2 9z" fill="var(--color-brand)" />
    <path d="M6 3l6 6 6-6M2 9h20M12 9v12" stroke="#fff" strokeOpacity=".6" strokeWidth="1.2" fill="none" />
  </svg>
);
export const XpIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M13 2 4 14h6l-1 8 9-12h-6z" fill="var(--color-accent)" stroke="var(--color-accent-ink)" strokeWidth="1.2" strokeLinejoin="round" />
  </svg>
);
export const StarIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="m12 2 3 6.5 7 .8-5.2 4.8 1.5 7L12 17.5 5.7 21l1.5-7L2 9.3l7-.8z" fill="currentColor" />
  </svg>
);
export const LockIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1zm2 0h6V7a3 3 0 0 0-6 0z" fill="currentColor" />
  </svg>
);
export const CheckIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="m5 12.5 4.5 4.5L19 7" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
  </svg>
);
export const CrossIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="4" strokeLinecap="round" fill="none" />
  </svg>
);
