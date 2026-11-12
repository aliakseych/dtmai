"use client";
import { useT } from "@/lib/i18n";
import { Input } from "./controls";

/** Content-language code input (regex `^[a-z]{2,3}(-[A-Za-z]{2,4})?$`); suggests the platform locales. */
export function LangInput({ value, onChange, id = "langs" }: { value: string; onChange: (v: string) => void; id?: string }) {
  const t = useT();
  return (
    <>
      <Input list={id} value={value} onChange={(e) => onChange(e.target.value)} placeholder={t("admin.lang.uzRuEn")} />
      <datalist id={id}>{["uz", "ru", "en", "uz-Latn", "uz-Cyrl"].map((l) => <option key={l} value={l} />)}</datalist>
    </>
  );
}
