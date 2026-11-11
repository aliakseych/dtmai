"use client";
import { useT } from "@dtmai/i18n";

export type NavCell = { id: string; answered: boolean; flagged: boolean };

/** Grid of question buttons with answered / marked states; the current one is outlined. */
export function QuestionNavigator({ cells, current, onGo }: { cells: NavCell[]; current: number; onGo: (i: number) => void }) {
  const t = useT();
  return (
    <div>
      <ul className="grid grid-cols-5 gap-2 sm:grid-cols-8 lg:grid-cols-5" aria-label={t("mock.nav")}>
        {cells.map((c, i) => {
          const state = c.flagged ? t("mock.stateFlagged") : c.answered ? t("mock.stateAnswered") : t("mock.stateEmpty");
          return (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => onGo(i)}
                aria-label={t("mock.navLabel", { n: i + 1, state })}
                aria-current={i === current ? "step" : undefined}
                className={`relative h-11 w-full rounded-xl border-2 font-extrabold ${
                  c.answered ? "border-blue-deep bg-blue-soft text-blue-deep" : "border-line bg-white text-ink-soft"
                } ${i === current ? "ring-2 ring-brand ring-offset-1" : ""}`}
              >
                {i + 1}
                {c.flagged && (
                  <span aria-hidden className="absolute -right-1 -top-1 grid h-4 w-4 place-items-center rounded-full bg-orange text-[10px] text-white">
                    ⚑
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 flex flex-wrap gap-4 text-xs font-bold text-ink-soft">
        <span className="flex items-center gap-1">
          <span aria-hidden className="h-3 w-3 rounded border-2 border-blue-deep bg-blue-soft" />
          {t("mock.legendAnswered")}
        </span>
        <span className="flex items-center gap-1">
          <span aria-hidden className="h-3 w-3 rounded-full bg-orange" />
          {t("mock.legendFlagged")}
        </span>
      </p>
    </div>
  );
}
