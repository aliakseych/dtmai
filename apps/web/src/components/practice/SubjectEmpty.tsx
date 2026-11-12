"use client";
import { Mascot } from "@dtmai/ui";
import { useLocale, useT } from "@dtmai/i18n";
import type { Subject } from "@/lib/api";
import { pick } from "@/lib/localized";

/** A subject has content unless the API reports zero verified questions (older API: field absent = has content). */
export function hasContent(s: Subject | undefined): boolean {
  return (s as { question_count?: number } | undefined)?.question_count !== 0;
}

/** Explains that a subject has no questions yet and offers the subjects that do (never a dead end). */
export function SubjectEmpty({ subjects, currentId, onPick }: { subjects: Subject[]; currentId: string; onPick: (id: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  const current = subjects.find((s) => s.id === currentId);
  const ready = subjects.filter((s) => s.id !== currentId && hasContent(s));
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border-2 border-line p-6 text-center">
      <Mascot mood="sad" size={96} alt="" className="h-auto w-20" />
      <h2 className="text-xl">{t("subject.empty.title", { subject: current ? pick(current.names, locale) : "" })}</h2>
      <p className="text-ink-soft">{t("subject.empty.text")}</p>
      <div className="flex w-full flex-col gap-2">
        {ready.map((s) => (
          <button key={s.id} type="button" onClick={() => onPick(s.id)} className="min-h-11 rounded-2xl border-2 border-b-4 border-line bg-white px-4 py-2 font-extrabold text-ink hover:bg-snow">
            {pick(s.names, locale)}
          </button>
        ))}
      </div>
    </div>
  );
}
