import { cn } from "../cn";
import { FlameIcon } from "./icons";

export function StreakFlame({ days, active = true, className }: { days: number; active?: boolean; className?: string }) {
  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <FlameIcon width={48} height={48} className={active ? "" : "grayscale opacity-50"} />
      <span className={cn("text-4xl font-extrabold", active ? "text-ink" : "text-ink-mute")}>{days}</span>
    </div>
  );
}
