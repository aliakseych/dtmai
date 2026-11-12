import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;
const base = { viewBox: "0 0 30 20", width: 30, height: 20, "aria-hidden": true } as const;

/** Flags are square-cornered; the consumer wrapper rounds and clips them. */
export const UzFlag = (p: P) => (
  <svg {...base} {...p}>
    <rect width="30" height="20" fill="#fff" />
    <rect width="30" height="6.2" fill="#0099b5" />
    <rect y="13.8" width="30" height="6.2" fill="#1eb53a" />
    <rect y="6.2" width="30" height="0.8" fill="#ce1126" />
    <rect y="13" width="30" height="0.8" fill="#ce1126" />
    <path d="M6.2 1.2a2.6 2.6 0 1 0 0 3.6 2.1 2.1 0 1 1 0-3.6z" fill="#fff" />
    <g fill="#fff">
      <circle cx="10" cy="1.9" r=".5" />
      <circle cx="12" cy="1.9" r=".5" />
      <circle cx="14" cy="1.9" r=".5" />
      <circle cx="11" cy="3.7" r=".5" />
      <circle cx="13" cy="3.7" r=".5" />
    </g>
  </svg>
);

export const RuFlag = (p: P) => (
  <svg {...base} {...p}>
    <rect width="30" height="20" fill="#fff" />
    <rect y="6.67" width="30" height="6.67" fill="#0039a6" />
    <rect y="13.33" width="30" height="6.67" fill="#d52b1e" />
  </svg>
);

export const GbFlag = (p: P) => (
  <svg {...base} {...p} overflow="hidden">
    <rect width="30" height="20" fill="#012169" />
    <path d="M0 0l30 20M30 0L0 20" stroke="#fff" strokeWidth="4" />
    <path d="M0 0l30 20M30 0L0 20" stroke="#c8102e" strokeWidth="1.6" />
    <path d="M15 0v20M0 10h30" stroke="#fff" strokeWidth="6.5" />
    <path d="M15 0v20M0 10h30" stroke="#c8102e" strokeWidth="3.6" />
  </svg>
);
