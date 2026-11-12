import type { ButtonHTMLAttributes } from "react";
import { cn } from "../cn";
import { CheckIcon, LockIcon, StarIcon } from "./icons";

export type PathNodeState = "locked" | "active" | "done" | "legendary";

const STATES: Record<PathNodeState, string> = {
  locked: "bg-line text-ink-mute border-line-deep",
  active: "bg-brand text-white border-brand-deep",
  done: "bg-accent text-ink border-accent-ink",
  legendary: "bg-brand text-white border-brand-deep",
};

export function PathNode({
  state,
  label,
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { state: PathNodeState; label: string }) {
  const locked = state === "locked";
  const Icon = locked ? LockIcon : state === "done" ? CheckIcon : StarIcon;
  return (
    <button
      type="button"
      aria-label={label}
      disabled={locked || rest.disabled}
      className={cn(
        "relative grid h-[72px] w-[72px] place-items-center rounded-full border-b-8 transition active:translate-y-1 active:border-b-4 disabled:cursor-not-allowed",
        STATES[state],
        state === "active" && "ring-4 ring-brand-soft",
        className,
      )}
      {...rest}
    >
      <Icon width={32} height={32} />
    </button>
  );
}
