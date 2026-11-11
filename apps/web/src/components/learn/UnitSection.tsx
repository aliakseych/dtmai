"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Mascot, cn } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import type { Path } from "@/lib/api";
import { TheoryCards, type TheoryCard } from "@/components/lesson/TheoryCards";
import { PathStep, type StepState } from "./PathStep";
import { OFFSETS, unitStyle } from "./unitStyle";

const stepState = (s: string, isCurrent: boolean): StepState => (s === "done" ? "completed" : s === "locked" ? "locked" : isCurrent ? "current" : "open");

/** One topic: sticky banner (UNIT N, title, THEORY) and its zig-zag lesson nodes with the mascot beside the gaps. */
export function UnitSection({ unit, index, fresh }: { unit: Path["units"][number]; index: number; fresh: Set<string> }) {
  const t = useT();
  const router = useRouter();
  const style = unitStyle(index);
  const [theoryOpen, setTheoryOpen] = useState(false);
  const theory: TheoryCard[] = unit.lessons.flatMap((l) => (l.has_theory ? (l.theory ?? []) : []));
  const ratio = unit.progress.total_lessons ? unit.progress.completed_lessons / unit.progress.total_lessons : 0;
  // Only the first open lesson is "current" (START); later open ones read as plain available nodes.
  const currentId = unit.lessons.find((l) => l.progress.state !== "done" && l.progress.state !== "locked")?.id;

  return (
    <section className="flex flex-col items-center">
      <div className={cn("sticky top-0 z-10 flex w-full items-center justify-between gap-3 rounded-card p-4 shadow-md", style.banner)}>
        <div className="min-w-0">
          <p className="text-sm font-extrabold uppercase tracking-wide opacity-80">
            {t("learn.unit", { n: index + 1 })} · {unit.progress.completed_lessons}/{unit.progress.total_lessons}
          </p>
          <h2 className="truncate text-xl">{unit.title}</h2>
        </div>
        {theory.length > 0 && (
          <button type="button" onClick={() => setTheoryOpen(true)} className="shrink-0 rounded-xl border-2 border-b-4 border-current bg-white/15 px-3 py-2 text-sm font-extrabold uppercase">
            {t("theory.button")}
          </button>
        )}
      </div>
      <div className="flex w-full max-w-md flex-col items-center py-4">
        {unit.lessons.map((l, i) => {
          const off = OFFSETS[i % OFFSETS.length];
          const state = stepState(l.progress.state, l.id === currentId);
          const status = t(state === "completed" ? "learn.node.done" : state === "locked" ? "learn.node.locked" : "learn.node.start");
          const side = i % OFFSETS.length === 2 ? "left" : i % OFFSETS.length === 6 ? "right" : null;
          return (
            <div key={l.id} className="relative flex w-full justify-center py-1.5" style={{ transform: `translateX(${off}px)` }}>
              {side && (
                <Mascot
                  mood={side === "left" ? "right" : "left"}
                  size={96}
                  alt=""
                  className={cn("pointer-events-none absolute top-1/2 hidden h-auto w-24 -translate-y-1/2 sm:block", side === "left" ? "-left-36" : "-right-36")}
                />
              )}
              <PathStep
                state={state}
                label={`${l.title} — ${status}`}
                title={l.title}
                progress={ratio}
                legendary={l.legendary}
                style={style}
                popped={fresh.has(l.id)}
                onOpen={() => router.push(`/lesson/${l.id}/`)}
              />
            </div>
          );
        })}
      </div>
      {theoryOpen && <TheoryCards cards={theory} title={unit.title} onDone={() => setTheoryOpen(false)} />}
    </section>
  );
}
