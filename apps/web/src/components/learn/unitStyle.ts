/** Unit colours cycle through the brand palette (primary, black, accent, deep primary). */
export type UnitStyle = { banner: string; node: string; ring: string };

const STYLES: UnitStyle[] = [
  { banner: "bg-brand text-white", node: "bg-brand border-brand-deep text-white", ring: "var(--color-brand)" },
  { banner: "bg-ink text-white", node: "bg-ink border-black text-white", ring: "var(--color-ink)" },
  { banner: "bg-accent text-ink", node: "bg-accent border-accent-deep text-ink", ring: "var(--color-accent-deep)" },
  { banner: "bg-brand-deep text-white", node: "bg-brand-deep border-ink text-white", ring: "var(--color-brand-deep)" },
];

export const unitStyle = (index: number): UnitStyle => STYLES[index % STYLES.length];

/** Horizontal zig-zag of the path nodes, px. */
export const OFFSETS = [0, 45, 70, 45, 0, -45, -70, -45];
