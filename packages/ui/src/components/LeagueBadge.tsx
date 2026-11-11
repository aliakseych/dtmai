import { cn } from "../cn";

const TIERS = ["bg-[#cd7f32]", "bg-[#b0b8c1]", "bg-gold", "bg-blue", "bg-green", "bg-brand", "bg-red", "bg-orange"];

/** tier is 0-based; names come from the API. */
export function LeagueBadge({ tier, name, size = 64, className }: { tier: number; name: string; size?: number; className?: string }) {
  return (
    <span
      role="img"
      aria-label={name}
      title={name}
      className={cn("grid place-items-center rounded-2xl border-b-4 border-black/20 font-extrabold text-white", TIERS[tier % TIERS.length], className)}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {tier + 1}
    </span>
  );
}
