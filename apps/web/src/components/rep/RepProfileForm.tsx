"use client";
import { useState } from "react";
import { Button, Card } from "@dtmai/ui";
import { LOCALES, LOCALE_LABELS, useT } from "@dtmai/i18n";
import type { DormitoryStatus } from "@/lib/api";
import { useLyceumDetail, type LyceumDetailData } from "@/components/lyceums/useLyceumDetail";
import { rep } from "./repApi";
import { repErrorKey } from "./repErrors";

const field = "w-full rounded-2xl border-2 border-line bg-snow px-4 py-3 text-ink focus:border-blue focus:bg-white";
const STATUSES: DormitoryStatus[] = ["unknown", "available", "limited", "none"];
const emptyMap = (src?: Record<string, string> | null) => Object.fromEntries(LOCALES.map((l) => [l, src?.[l] ?? ""]));
const clean = (m: Record<string, string>) => Object.fromEntries(Object.entries(m).filter(([, v]) => v.trim()).map(([k, v]) => [k, v.trim()]));

function Form({ detail, onSaved }: { detail: LyceumDetailData; onSaved: () => void }) {
  const t = useT();
  const p = detail.profile;
  const contacts = p.contacts;
  const [description, setDescription] = useState(emptyMap(p.description));
  const [courses, setCourses] = useState(p.courses.join("\n"));
  const [phone, setPhone] = useState(contacts.phone ?? "");
  const [telegram, setTelegram] = useState(contacts.telegram ?? "");
  const [email, setEmail] = useState(contacts.email ?? "");
  const [status, setStatus] = useState<DormitoryStatus>(p.dormitory_status);
  const [dorm, setDorm] = useState(emptyMap(p.dormitory_description));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setSaved(false);
    try {
      await rep.updateProfile(detail.id, {
        description: clean(description),
        courses: courses.split("\n").map((c) => c.trim()).filter(Boolean),
        contacts: { phone: phone.trim() || null, telegram: telegram.trim() || null, email: email.trim() || null },
        dormitory_status: status,
        dormitory_description: clean(dorm),
      });
      setSaved(true);
      onSaved();
    } catch (e2) {
      setErr(t(repErrorKey(e2)));
    } finally {
      setBusy(false);
    }
  };

  const perLocale = (label: string, map: Record<string, string>, set: (m: Record<string, string>) => void) => (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-bold text-ink-soft">{label}</legend>
      {LOCALES.map((l) => (
        <label key={l} className="flex flex-col gap-1">
          <span className="text-xs font-bold text-ink-soft">{LOCALE_LABELS[l]}</span>
          <textarea rows={3} value={map[l] ?? ""} onChange={(e) => set({ ...map, [l]: e.target.value })} className={field} />
        </label>
      ))}
    </fieldset>
  );

  return (
    <Card>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <h2 className="text-xl text-ink">{t("rep.profile.title")}</h2>
        {perLocale(t("rep.profile.description"), description, setDescription)}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.profile.courses")}</span>
          <textarea rows={4} value={courses} onChange={(e) => setCourses(e.target.value)} placeholder={t("rep.profile.coursesHint")} className={field} />
        </label>
        <fieldset className="grid gap-3 sm:grid-cols-3">
          <legend className="mb-1 text-sm font-bold text-ink-soft">{t("rep.profile.contacts")}</legend>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} aria-label={t("rep.profile.phone")} placeholder={t("rep.profile.phone")} className={field} />
          <input value={telegram} onChange={(e) => setTelegram(e.target.value)} aria-label={t("rep.profile.telegram")} placeholder={t("rep.profile.telegram")} className={field} />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} aria-label={t("rep.profile.email")} placeholder={t("rep.profile.email")} className={field} />
        </fieldset>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-bold text-ink-soft">{t("rep.profile.dormitory")}</span>
          <select value={status} onChange={(e) => setStatus(e.target.value as DormitoryStatus)} className={field}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{t(`lyceums.dorm.${s}` as const)}</option>
            ))}
          </select>
        </label>
        {perLocale(t("rep.profile.dormDescription"), dorm, setDorm)}
        {err && <p role="alert" className="text-sm font-bold text-red-deep">{err}</p>}
        {saved && <p role="status" className="text-sm font-bold text-brand">{t("rep.profile.saved")}</p>}
        <div>
          <Button type="submit" disabled={busy}>{t("rep.profile.save")}</Button>
        </div>
      </form>
    </Card>
  );
}

/** Approved-rep editor for the lyceum profile: description, courses, contacts and dormitory. */
export function RepProfileForm({ lyceumId }: { lyceumId: string }) {
  const t = useT();
  const { data, reload } = useLyceumDetail(lyceumId);
  if (data === undefined) return <p className="py-4 text-center text-ink-soft">{t("common.loading")}</p>;
  if (data === null) return <p role="alert" className="py-4 text-center text-ink-soft">{t("common.error")}</p>;
  return <Form detail={data} onSaved={reload} />;
}
