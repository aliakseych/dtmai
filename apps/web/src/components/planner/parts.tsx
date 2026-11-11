"use client";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { buttonClass, cn } from "@dtmai/ui";
import { useT, type MessageKey } from "@dtmai/i18n";
import { completeTask, taskHref, type TaskKind, type TaskOut } from "@/lib/planner";

/** Circular progress; the stroke animates in unless the user prefers reduced motion. */
export function ProgressRing({
  value,
  max,
  size = 96,
  stroke = 10,
  className,
  children,
}: {
  value: number;
  max: number;
  size?: number;
  stroke?: number;
  className?: string;
  children?: ReactNode;
}) {
  const reduce = useReducedMotion();
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const frac = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  return (
    <div className={cn("relative grid shrink-0 place-items-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={stroke} className="stroke-line" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          className="stroke-accent"
          strokeDasharray={c}
          initial={{ strokeDashoffset: reduce ? c * (1 - frac) : c }}
          animate={{ strokeDashoffset: c * (1 - frac) }}
          transition={reduce ? { duration: 0 } : { duration: 0.9, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">{children}</div>
    </div>
  );
}

/** Filled circle with a tick that pops in with a spring. */
export function BouncyCheck({ size = 28, className }: { size?: number; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.span
      aria-hidden="true"
      initial={reduce ? false : { scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 500, damping: 14 }}
      className={cn("grid shrink-0 place-items-center rounded-full bg-accent text-ink", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
        <path d="m5 12.5 4.5 4.5L19 7" />
      </svg>
    </motion.span>
  );
}

const KIND_ICON: Record<TaskKind, string> = {
  lesson: "/brand/icon-lesson.png",
  drill: "/brand/icon-xp.png",
  review: "/brand/icon-review.png",
  mock: "/brand/icon-mock.png",
  rush: "/brand/icon-xp.png",
};
export const KIND_DOT: Record<TaskKind, string> = {
  lesson: "bg-blue",
  drill: "bg-gold",
  review: "bg-red",
  mock: "bg-accent",
  rush: "bg-gold",
};
export const KIND_LABEL: Record<TaskKind, MessageKey> = {
  lesson: "plan.task.lesson",
  drill: "plan.task.drill",
  review: "plan.task.review",
  mock: "plan.task.mock",
  rush: "plan.task.rush",
};

/** Rounded, filled icon tile for a task kind. */
export function KindIcon({ kind, className }: { kind: TaskKind; className?: string }) {
  return (
    <span aria-hidden="true" className={cn("grid size-12 shrink-0 place-items-center rounded-2xl border-2 border-line bg-snow", className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={KIND_ICON[kind]} alt="" width={32} height={32} className="size-8 object-contain" />
    </span>
  );
}

/** One planned task: icon, title, subject/minutes, then a tick (done) or a start link (todo). */
export function TaskCard({ task, onOpen, onDone }: { task: TaskOut; onOpen?: () => void; onDone?: () => void }) {
  const t = useT();
  const href = taskHref(task.kind);
  const [optimistic, setOptimistic] = useState(false);
  const done = task.status === "done" || optimistic;
  const open = !done;
  const markDone = () => {
    setOptimistic(true);
    completeTask(task.id).then(onDone, () => setOptimistic(false));
  };
  const meta = [task.subject_name, `${task.est_minutes} ${t("plan.min")}`].filter(Boolean).join(" · ");
  const body = (
    <>
      <KindIcon kind={task.kind} />
      <span className="min-w-0 flex-1 text-left">
        <span className="block text-xs font-extrabold uppercase text-ink-soft">{t(KIND_LABEL[task.kind])}</span>
        <span className={cn("block break-words font-extrabold", !open && "text-ink-soft line-through")}>{task.subject_name ?? t(KIND_LABEL[task.kind])}</span>
        <span className="block text-sm text-ink-soft">{meta}</span>
      </span>
    </>
  );
  return (
    <li className={cn("flex flex-wrap items-center gap-3 rounded-card border-2 p-3", done ? "border-accent bg-accent-soft" : "border-line bg-white")}>
      {onOpen ? (
        <button type="button" onClick={onOpen} className="flex min-w-0 flex-1 items-center gap-3 rounded-xl text-left">
          {body}
        </button>
      ) : (
        <div className="flex min-w-0 flex-1 items-center gap-3">{body}</div>
      )}
      {done && <BouncyCheck />}
      {open && (
        <div className="flex w-full gap-2 [&>*]:flex-1">
          <button type="button" onClick={markDone} className={buttonClass("secondary", false, "px-3 py-2 text-sm")}>
            {t("plan.markDone")}
          </button>
          <Link href={href} className={buttonClass("primary", false, "px-4 py-2 text-sm")}>
            {t("common.start")}
          </Link>
        </div>
      )}
    </li>
  );
}
