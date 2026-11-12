"use client";
import { useT, type MessageKey } from "@dtmai/i18n";
import { useFieldLabel } from "./useFieldLabel";
import type { LyceumDetailData } from "./useLyceumDetail";

type Admission = LyceumDetailData["admission"];

const langOf = (r: Admission["plan"][number], t: (k: MessageKey) => string) => {
  const names = [r.seats_uz > 0 && t("lyceums.admission.uz"), r.seats_ru > 0 && t("lyceums.admission.ru"), r.seats_qq > 0 && t("lyceums.admission.qq")].filter(Boolean);
  return names.length ? names.join(", ") : "—";
};

/** Seats per direction and language of instruction, applicants per seat, and phone / Telegram links. */
export function AdmissionSeats({ admission: a }: { admission: Admission }) {
  const t = useT();
  const label = useFieldLabel();
  const contact = a.contact;
  const hasContact = !!contact && (contact.phones.length > 0 || !!contact.telegram);
  if (a.plan.length === 0 && !hasContact) return null;
  return (
    <>
      {a.plan.length > 0 && (
        <section aria-label={t("lyceums.admission.title")}>
          <h3 className="mb-2 text-lg text-ink">
            {t("lyceums.admission.title")}
            {a.year ? ` · ${a.year}` : ""}
          </h3>
          <p className="mb-2 text-ink-soft">
            {t("lyceums.admission.seatsTotal", { count: a.seats_total })}
            {a.ratio != null && (
              <span className="ml-2 font-extrabold text-brand">
                {t("lyceums.admission.ratio")}: {a.ratio.toFixed(1)}
              </span>
            )}
          </p>
          <div className="max-w-full overflow-x-auto" tabIndex={0}>
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="text-ink-soft">
                <tr>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.direction")}</th>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.language")}</th>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.uz")}</th>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.ru")}</th>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.qq")}</th>
                  <th scope="col" className="py-1 pr-2">{t("lyceums.admission.total")}</th>
                  <th scope="col" className="py-1">{t("lyceums.admission.ratio")}</th>
                </tr>
              </thead>
              <tbody>
                {a.plan.map((r) => (
                  <tr key={`${r.direction_code}-${r.language_name ?? ""}`} className="border-t border-line">
                    <td className="py-1 pr-2">
                      {(() => {
                        const f = label(r.direction_code);
                        return (
                          <>
                            {f.name}
                            {f.subjects && <span className="block text-xs text-ink-soft">{f.subjects}</span>}
                          </>
                        );
                      })()}
                    </td>
                    <td className="py-1 pr-2">{r.language_name ?? langOf(r, t)}</td>
                    <td className="py-1 pr-2">{r.seats_uz}</td>
                    <td className="py-1 pr-2">{r.seats_ru}</td>
                    <td className="py-1 pr-2">{r.seats_qq}</td>
                    <td className="py-1 pr-2 font-bold">{r.seats_total}</td>
                    <td className="py-1">{r.ratio != null ? r.ratio.toFixed(1) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {a.ratio != null && a.applications_year && (
            <p className="mt-2 text-xs text-ink-soft">
              {t("lyceums.admission.ratioHint", { year: a.applications_year })}
            </p>
          )}
        </section>
      )}
      {hasContact && contact && (
        <section aria-label={t("lyceums.admission.contacts")}>
          <h3 className="mb-2 text-lg text-ink">{t("lyceums.admission.contacts")}</h3>
          <ul className="flex flex-wrap gap-2">
            {contact.phones.map((p) => (
              <li key={p}>
                <a href={`tel:${p}`} className="inline-flex min-h-11 items-center rounded-xl border-2 border-line px-3 font-bold text-brand">
                  {p}
                </a>
              </li>
            ))}
            {contact.telegram && (
              <li>
                <a
                  href={contact.telegram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-11 items-center rounded-xl border-2 border-line px-3 font-bold text-brand"
                >
                  {t("lyceums.admission.telegram")}
                </a>
              </li>
            )}
          </ul>
        </section>
      )}
    </>
  );
}
