import type { ReactNode } from "react";
import { cn } from "../cn";
import { CheckIcon, CrossIcon } from "./icons";

export type SheetTone = "correct" | "incorrect";

export function Sheet({
  tone,
  title,
  children,
  action,
  mascot,
  className,
}: {
  tone: SheetTone;
  title: string;
  children?: ReactNode;
  action: ReactNode;
  /** Optional mascot image shown beside the title */
  mascot?: ReactNode;
  className?: string;
}) {
  const ok = tone === "correct";
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "sheet-in w-full border-t-2 px-4 pt-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:px-8",
        ok ? "border-green-soft bg-green-soft text-[#2f6200]" : "border-red-soft bg-red-soft text-[#a11c1c]",
        className,
      )}
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className={cn("grid h-12 w-12 shrink-0 place-items-center rounded-full bg-white", ok ? "text-green-deep" : "text-red-deep")}>
            {ok ? <CheckIcon /> : <CrossIcon />}
          </span>
          <div>
            <p className="text-xl font-extrabold">{title}</p>
            {children && <div className="text-[15px]">{children}</div>}
          </div>
        </div>
        {mascot}
        <div className="sm:w-48">{action}</div>
      </div>
    </div>
  );
}
