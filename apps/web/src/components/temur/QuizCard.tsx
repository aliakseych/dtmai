"use client";
import { useState } from "react";
import { OptionGroup, OptionTile } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";
import { RichText } from "@/components/RichText";
import type { TutorQuiz } from "@/lib/api";

/** Inline quiz from Temur; answered and checked on the client against `correct_index`. */
export function QuizCard({ quiz }: { quiz: TutorQuiz }) {
  const t = useT();
  const [picked, setPicked] = useState<number | null>(null);
  const done = picked !== null;
  return (
    <div className="mt-3 flex flex-col gap-3 rounded-2xl border-2 border-line bg-white p-4 text-ink">
      <p className="font-extrabold">
        <RichText text={quiz.stem} />
      </p>
      <OptionGroup label={t("temur.quiz")} className="flex flex-col gap-2">
        {quiz.options.map((o, i) => (
          <OptionTile
            key={i}
            index={i}
            disabled={done}
            state={!done ? "idle" : i === quiz.correct_index ? "correct" : i === picked ? "incorrect" : "idle"}
            onSelect={() => setPicked(i)}
          >
            <RichText text={o} />
          </OptionTile>
        ))}
      </OptionGroup>
      {done && (
        <div role="status" className="flex flex-col gap-1">
          <strong className={picked === quiz.correct_index ? "text-brand" : "text-red-deep"}>
            {picked === quiz.correct_index ? t("lesson.correct") : t("lesson.incorrect")}
          </strong>
          {quiz.explanation && (
            <span className="text-ink-soft">
              <RichText text={quiz.explanation} />
            </span>
          )}
        </div>
      )}
    </div>
  );
}
