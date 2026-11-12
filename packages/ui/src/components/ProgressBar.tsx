import { cn } from "../cn";

export function ProgressBar({
  value,
  max = 100,
  color = "bg-brand",
  label,
  className,
}: {
  value: number;
  max?: number;
  color?: string;
  label?: string;
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, max === 0 ? 0 : (value / max) * 100));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      className={cn("h-4 w-full overflow-hidden rounded-full bg-line", className)}
    >
      <div className={cn("h-full rounded-full transition-[width] duration-300", color)} style={{ width: `${pct}%` }}>
        <div className="mx-2 mt-1 h-1 rounded-full bg-white/30" />
      </div>
    </div>
  );
}
