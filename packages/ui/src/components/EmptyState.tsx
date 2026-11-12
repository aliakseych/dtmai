import type { ReactNode } from "react";
import { cn } from "../cn";
import { Mascot, type MascotMood } from "./Mascot";

/** Empty / locked / error placeholder: mascot, title, optional body and one action.
 *  `compact` is the in-card variant: dashed box, text only. */
export function EmptyState({
  mood = "point",
  title,
  body,
  action,
  compact = false,
  basePath,
  className,
}: {
  mood?: MascotMood;
  title: ReactNode;
  body?: ReactNode;
  action?: ReactNode;
  compact?: boolean;
  basePath?: string;
  className?: string;
}) {
  if (compact) {
    return (
      <div className={cn("flex flex-col items-center gap-2 rounded-card border-2 border-dashed border-line p-4 text-center", className)}>
        <p className="font-extrabold text-ink-soft">{title}</p>
        {body ? <p className="text-sm text-ink-soft">{body}</p> : null}
        {action}
      </div>
    );
  }
  return (
    <div className={cn("flex flex-col items-center gap-3 py-8 text-center", className)}>
      <Mascot mood={mood} size={120} alt="" basePath={basePath} />
      <p className="text-lg font-extrabold">{title}</p>
      {body ? <p className="max-w-sm text-ink-soft">{body}</p> : null}
      {action}
    </div>
  );
}
