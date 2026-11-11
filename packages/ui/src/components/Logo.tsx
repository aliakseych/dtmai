import { cn } from "../cn";

/**
 * DTM AI banner wordmark: bold italic name inside a slanted outlined box.
 * `tone="brand"` = #100FA0 on light surfaces, `tone="light"` = white on brand-coloured ones.
 */
export function Logo({
  name = "DTM AI",
  tone = "brand",
  size = 32,
  className,
}: {
  name?: string;
  tone?: "brand" | "light";
  /** Height of the mark in px; the width follows the 10:3 aspect. */
  size?: number;
  className?: string;
}) {
  return (
    <svg
      role="img"
      aria-label={name}
      viewBox="0 0 150 46"
      height={size}
      width={(size * 150) / 46}
      className={cn("shrink-0 select-none", tone === "brand" ? "text-brand" : "text-white", className)}
    >
      <polygon points="14,3 147,3 136,43 3,43" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinejoin="round" />
      <text
        x="75"
        y="32"
        textAnchor="middle"
        fill="currentColor"
        fontStyle="italic"
        fontWeight={900}
        fontSize="26"
        textLength="100"
        lengthAdjust="spacingAndGlyphs"
        style={{ fontFamily: "var(--font-nunito), Nunito, system-ui, sans-serif" }}
      >
        {name}
      </text>
    </svg>
  );
}
