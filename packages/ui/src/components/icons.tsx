import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;
const base = { viewBox: "0 0 24 24", width: 24, height: 24, "aria-hidden": true } as const;

export const FlameIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-4 2-7 1 1 2 2 2.5 3C11 8 11 5 12 2z" fill="#ff9600" />
    <path d="M12 12c1 2 3 2.5 3 5a3 3 0 0 1-6 0c0-2 2-2.5 3-5z" fill="#ffc800" />
  </svg>
);
export const HeartIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z" fill="#ff4b4b" />
  </svg>
);
export const GemIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M6 3h12l4 6-10 12L2 9z" fill="#1cb0f6" />
    <path d="M6 3l6 6 6-6M2 9h20M12 9v12" stroke="#fff" strokeOpacity=".6" strokeWidth="1.2" fill="none" />
  </svg>
);
export const XpIcon = (p: P) => (
  <svg {...base} {...p}>
    <path d="M13 2 4 14h6l-1 8 9-12h-6z" fill="#ffc800" />
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
