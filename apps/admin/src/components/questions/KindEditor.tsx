"use client";
import { Icon } from "@dtmai/ui";
import { useT } from "@/lib/i18n";
import { Btn, Check, Field, Input, Select, Textarea } from "@/components/ui/controls";
import { Md } from "@/components/ui/markdown";
import { uploadMedia } from "@/lib/media";
import { mediaUrl } from "@/lib/env";
import { useToast } from "@dtmai/ui";
import { errMsg, uuid } from "@/lib/util";
import type { Draft, Opt } from "@/lib/questions";

const nextId = (list: Opt[], prefix: string) => `${prefix}${list.length + 1}${uuid().slice(0, 2)}`;

function OptList({ title, list, onChange, prefix, marker }: { title: string; list: Opt[]; onChange: (l: Opt[]) => void; prefix: string; marker?: (o: Opt) => React.ReactNode }) {
  const t = useT();
  const toast = useToast();
  const upd = (i: number, p: Partial<Opt>) => onChange(list.map((o, j) => (j === i ? { ...o, ...p } : o)));
  const upload = async (i: number, f?: File) => {
    if (!f) return;
    try { upd(i, { media: (await uploadMedia(f)).key }); } catch (e) { toast(errMsg(e), "error"); }
  };
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between"><h4 className="text-xs font-extrabold uppercase text-ink-soft">{title}</h4><Btn onClick={() => onChange([...list, { id: nextId(list, prefix), text: "" }])}>{t("admin.questions.add")}</Btn></div>
      {list.map((o, i) => (
        <div key={i} className="grid grid-cols-[auto_4rem_1fr_auto_auto] sm:grid-cols-[auto_5rem_1fr_auto_auto] items-center gap-2">
          <span>{marker?.(o)}</span>
          <Input aria-label={t("admin.questions.id")} value={o.id} onChange={(e) => upd(i, { id: e.target.value })} />
          <div className="min-w-0">
            <Input aria-label={t("admin.questions.text")} value={o.text} onChange={(e) => upd(i, { text: e.target.value })} />
            {o.text.includes("$") && <div className="mt-0.5 text-xs text-ink-soft"><Md text={o.text} /></div>}
            {o.media && <img alt="" src={mediaUrl(o.media)} className="mt-1 max-h-16 rounded border border-line" />}
          </div>
          <label className="cursor-pointer rounded border border-line px-1.5 py-1 text-xs hover:bg-snow">{t("admin.questions.img")}<input type="file" accept="image/*" hidden onChange={(e) => upload(i, e.target.files?.[0])} /></label>
          <Btn variant="ghost" aria-label={t("admin.common.remove")} onClick={() => onChange(list.filter((_, j) => j !== i))}><Icon name="close" size={16} /></Btn>
        </div>
      ))}
    </div>
  );
}

export function KindEditor({ d, onChange }: { d: Draft; onChange: (d: Draft) => void }) {
  const t = useT();
  const set = (p: Partial<Draft>) => onChange({ ...d, ...p });
  switch (d.kind) {
    case "single_choice":
    case "multi_choice": {
      const multi = d.kind === "multi_choice";
      const toggle = (id: string) => set({ correct: multi ? (d.correct.includes(id) ? d.correct.filter((x) => x !== id) : [...d.correct, id]) : [id] });
      return <OptList title={multi ? t("admin.questions.optionsMarkAll") : t("admin.questions.optionsMarkOne")} list={d.options} prefix="o" onChange={(options) => set({ options })}
        marker={(o) => <input type={multi ? "checkbox" : "radio"} name="correct" aria-label={t("admin.questions.isCorrect", { id: o.id })} className="accent-green" checked={d.correct.includes(o.id)} onChange={() => toggle(o.id)} />} />;
    }
    case "numeric":
      return <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Field label={t("admin.common.value")}><Input inputMode="decimal" value={d.value} onChange={(e) => set({ value: e.target.value })} /></Field>
        <Field label={t("admin.questions.tolerance")} hint={t("admin.questions.optional")}><Input inputMode="decimal" value={d.tolerance} onChange={(e) => set({ tolerance: e.target.value })} /></Field>
        <Field label={t("admin.questions.unit")} hint={t("admin.questions.shownAfterTheInput")}><Input value={d.unit} onChange={(e) => set({ unit: e.target.value })} /></Field>
      </div>;
    case "short_text":
      return <div className="space-y-2">
        <Field label={t("admin.questions.acceptedAnswers")} hint={t("admin.questions.onePerLine")}><Textarea rows={4} value={d.accepted} onChange={(e) => set({ accepted: e.target.value })} /></Field>
        <Check checked={d.caseSensitive} onChange={(caseSensitive) => set({ caseSensitive })} label={t("admin.questions.caseSensitive")} />
      </div>;
    case "matching":
      return <div className="space-y-3">
        <OptList title={t("admin.questions.left")} list={d.left} prefix="l" onChange={(left) => set({ left })} />
        <OptList title={t("admin.questions.right")} list={d.right} prefix="r" onChange={(right) => set({ right })} />
        <div className="space-y-1"><h4 className="text-xs font-extrabold uppercase text-ink-soft">{t("admin.questions.correctPairs")}</h4>
          {d.left.map((l) => (
            <div key={l.id} className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-sm">
              <span className="truncate">{l.text || l.id}</span>→
              <Select value={d.pairs[l.id] ?? ""} onChange={(e) => set({ pairs: { ...d.pairs, [l.id]: e.target.value } })}><option value="">—</option>{d.right.map((r) => <option key={r.id} value={r.id}>{r.text || r.id}</option>)}</Select>
            </div>
          ))}
        </div>
      </div>;
    case "ordering":
      return <div className="space-y-1">
        <p className="text-xs text-ink-soft">{t("admin.questions.listItemsInTheir")} <b>{t("admin.questions.correctOrder")}</b>{t("admin.questions.theLearnerSeesThem")}</p>
        <OptList title={t("admin.questions.itemsCorrectOrder")} list={d.items} prefix="i" onChange={(items) => set({ items })} marker={(o) => <span className="text-xs font-extrabold text-ink-soft">{d.items.findIndex((x) => x.id === o.id) + 1}</span>} />
        <div className="flex gap-1">{d.items.map((_, i) => i > 0 && <Btn key={i} onClick={() => { const it = [...d.items]; [it[i - 1], it[i]] = [it[i], it[i - 1]]; set({ items: it }); }}>↑ {i + 1}</Btn>)}</div>
      </div>;
    case "passage_group":
      return <Field label={t("admin.questions.childQuestionIds")} hint={t("admin.questions.oneUuidPerLine")}><Textarea rows={5} value={d.childIds} onChange={(e) => set({ childIds: e.target.value })} /></Field>;
  }
}
