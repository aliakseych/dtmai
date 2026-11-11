import { cn } from "../cn";

/**
 * DTM AI wordmark with an accent mark (lime tile with a brand check).
 * `tone="brand"` for light surfaces, `tone="light"` for brand-coloured ones.
 */
export function Logo({
  name = "DTM AI",
  tone = "brand",
  size = 32,
  className,
}: {
  name?: string;
  tone?: "brand" | "light";
  /** Height of the mark in px; the wordmark scales with it. */
  size?: number;
  className?: string;
}) {
  const [first, ...rest] = name.split(" ");
  const second = rest.join(" ");
  return (
    <span
      role="img"
      aria-label={name}
      className={cn("inline-flex select-none items-center gap-2 font-extrabold leading-none tracking-tight", className)}
      style={{ fontSize: size * 0.8 }}
    >
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
        <rect width="32" height="32" rx="9" fill="#aff50b" />
        <path d="M8 17.5l5.5 5.5L24.5 9" fill="none" stroke="#100fa0" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span aria-hidden className={tone === "brand" ? "text-brand" : "text-white"}>
        {first}
        {second && <span className={tone === "brand" ? "text-black" : "text-accent"}> {second}</span>}
      </span>
    </span>
  );
}
