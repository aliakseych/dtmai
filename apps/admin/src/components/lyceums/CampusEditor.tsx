import { useT } from "@/lib/i18n";
import { Icon } from "@dtmai/ui";
import type { LyceumPatch } from "@/lib/lyceums";
import { LOCALE_LIST } from "@/lib/util";
import { Btn, Field, Input, Textarea } from "@/components/ui/controls";
import { ImageSlot } from "./ProfileEditor";

type Names = Record<string, string>;
export interface CampusForm {
  lat: string; lng: string; embedUrl: string; mapImage: string;
  buildings: { name: Names; plans: { label: Names; image: string }[] }[];
  specs: { field: string; name: Names; desc: Names; subjects: Names[] }[];
  offerings: { title: Names; desc: Names; by: Names }[];
}

type P = NonNullable<LyceumPatch["buildings"]>;
const clean = (n: Names): Names => Object.fromEntries(Object.entries(n).filter(([, v]) => v.trim()));

/** Form state -> patch body fields. */
export function campusPatch(c: CampusForm): Pick<LyceumPatch, "map" | "buildings" | "specializations" | "offerings"> {
  const num = (s: string) => (s.trim() ? Number(s) : null);
  return {
    map: { lat: num(c.lat), lng: num(c.lng), embed_url: c.embedUrl.trim() || null, image_url: c.mapImage || null },
    buildings: c.buildings.map((b): P[number] => ({
      name: clean(b.name),
      floor_plans: b.plans.map((p) => ({ label: clean(p.label), image_url: p.image })),
    })),
    specializations: c.specs.map((s) => ({
      field_code: s.field.trim(), name: clean(s.name), description: clean(s.desc),
      second_year_subjects: s.subjects.map(clean).filter((x) => Object.keys(x).length),
    })),
    offerings: c.offerings.map((o) => ({ title: clean(o.title), description: clean(o.desc), taught_by: clean(o.by) })),
  };
}

type Detail = { map?: { lat?: number | null; lng?: number | null; embed_url?: string | null; image_url?: string | null } | null } & Pick<
  import("@/lib/lyceums").LyceumDetail["profile"], "buildings" | "specializations" | "offerings"
>;

export function campusForm(p: Detail): CampusForm {
  return {
    lat: p.map?.lat?.toString() ?? "", lng: p.map?.lng?.toString() ?? "", embedUrl: p.map?.embed_url ?? "", mapImage: p.map?.image_url ?? "",
    buildings: p.buildings.map((b) => ({ name: { ...b.name }, plans: (b.floor_plans ?? []).map((f) => ({ label: { ...f.label }, image: f.image_url })) })),
    specs: p.specializations.map((s) => ({ field: s.field_code, name: { ...s.name }, desc: { ...s.description }, subjects: (s.second_year_subjects ?? []).map((x) => ({ ...x })) })),
    offerings: p.offerings.map((o) => ({ title: { ...o.title }, desc: { ...o.description }, by: { ...o.taught_by } })),
  };
}

/** One text input per content locale. */
function Localized({ label, value, onChange, area }: { label: string; value: Names; onChange: (v: Names) => void; area?: boolean }) {
  return (
    <fieldset className="space-y-1">
      <legend className="text-xs font-bold text-ink-soft">{label}</legend>
      {LOCALE_LIST.map((l) => {
        const props = { value: value[l] ?? "", placeholder: l, "aria-label": `${label} ${l}`, onChange: (e: { target: { value: string } }) => onChange({ ...value, [l]: e.target.value }) };
        return area ? <Textarea key={l} className="font-sans" {...props} /> : <Input key={l} {...props} />;
      })}
    </fieldset>
  );
}

function RemoveBtn({ onClick }: { onClick: () => void }) {
  const t = useT();
  return <button type="button" aria-label={t("admin.common.remove")} onClick={onClick} className="grid size-11 place-items-center rounded-full text-red"><Icon name="close" size={20} /></button>;
}

const move = <T,>(arr: T[], i: number, v: T | null) => (v === null ? arr.filter((_, j) => j !== i) : arr.map((x, j) => (j === i ? v : x)));

export function CampusEditor({ value: c, onChange }: { value: CampusForm; onChange: (c: CampusForm) => void }) {
  const t = useT();
  const set = (p: Partial<CampusForm>) => onChange({ ...c, ...p });
  const box = "space-y-2 rounded-xl border border-line p-2";
  const legend = "px-1 text-xs font-extrabold uppercase tracking-wide text-ink-soft";
  return (
    <div className="space-y-4">
      <fieldset className={box}>
        <legend className={legend}>{t("admin.lyceums.map")}</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={t("admin.lyceums.mapLat")}><Input inputMode="decimal" value={c.lat} onChange={(e) => set({ lat: e.target.value })} /></Field>
          <Field label={t("admin.lyceums.mapLng")}><Input inputMode="decimal" value={c.lng} onChange={(e) => set({ lng: e.target.value })} /></Field>
          <Field label={t("admin.lyceums.mapEmbed")} className="sm:col-span-2"><Input type="url" value={c.embedUrl} onChange={(e) => set({ embedUrl: e.target.value })} placeholder={t("admin.lyceums.https")} /></Field>
        </div>
        <ImageSlot label={t("admin.lyceums.mapImage")} value={c.mapImage} onChange={(mapImage) => set({ mapImage })} />
      </fieldset>

      <fieldset className={box}>
        <legend className={legend}>{t("admin.lyceums.buildings")}</legend>
        {c.buildings.map((b, i) => (
          <div key={i} className="space-y-2 rounded-xl border border-line p-2">
            <div className="flex items-start gap-2">
              <div className="flex-1"><Localized label={t("admin.lyceums.buildingName")} value={b.name} onChange={(name) => set({ buildings: move(c.buildings, i, { ...b, name }) })} /></div>
              <RemoveBtn onClick={() => set({ buildings: move(c.buildings, i, null) })} />
            </div>
            {b.plans.map((p, j) => (
              <div key={j} className="flex items-start gap-2 rounded-lg bg-snow p-2">
                <div className="flex-1 space-y-2">
                  <ImageSlot label={t("admin.lyceums.floorPlan")} value={p.image} onChange={(image) => set({ buildings: move(c.buildings, i, { ...b, plans: move(b.plans, j, { ...p, image }) }) })} />
                  {!p.image && <p role="alert" className="text-xs font-bold text-red">{t("admin.lyceums.floorPlanImageRequired")}</p>}
                  <Localized label={t("admin.lyceums.floorPlanLabel")} value={p.label} onChange={(label) => set({ buildings: move(c.buildings, i, { ...b, plans: move(b.plans, j, { ...p, label }) }) })} />
                </div>
                <RemoveBtn onClick={() => set({ buildings: move(c.buildings, i, { ...b, plans: move(b.plans, j, null) }) })} />
              </div>
            ))}
            <Btn onClick={() => set({ buildings: move(c.buildings, i, { ...b, plans: [...b.plans, { label: {}, image: "" }] }) })}>{t("admin.lyceums.addFloorPlan")}</Btn>
          </div>
        ))}
        <Btn onClick={() => set({ buildings: [...c.buildings, { name: {}, plans: [] }] })}>{t("admin.lyceums.addBuilding")}</Btn>
      </fieldset>

      <fieldset className={box}>
        <legend className={legend}>{t("admin.lyceums.specializations")}</legend>
        {c.specs.map((s, i) => (
          <div key={i} className="space-y-2 rounded-xl border border-line p-2">
            <div className="flex items-start gap-2">
              <Field label={t("admin.lyceums.specField")} className="flex-1"><Input value={s.field} onChange={(e) => set({ specs: move(c.specs, i, { ...s, field: e.target.value }) })} /></Field>
              <RemoveBtn onClick={() => set({ specs: move(c.specs, i, null) })} />
            </div>
            <Localized label={t("admin.lyceums.specName")} value={s.name} onChange={(name) => set({ specs: move(c.specs, i, { ...s, name }) })} />
            <Localized area label={t("admin.lyceums.description")} value={s.desc} onChange={(desc) => set({ specs: move(c.specs, i, { ...s, desc }) })} />
            {s.subjects.map((x, j) => (
              <div key={j} className="flex items-start gap-2 rounded-lg bg-snow p-2">
                <div className="flex-1"><Localized label={t("admin.lyceums.specSubject")} value={x} onChange={(v) => set({ specs: move(c.specs, i, { ...s, subjects: move(s.subjects, j, v) }) })} /></div>
                <RemoveBtn onClick={() => set({ specs: move(c.specs, i, { ...s, subjects: move(s.subjects, j, null) }) })} />
              </div>
            ))}
            <Btn onClick={() => set({ specs: move(c.specs, i, { ...s, subjects: [...s.subjects, {}] }) })}>{t("admin.lyceums.addSpecSubject")}</Btn>
          </div>
        ))}
        <Btn onClick={() => set({ specs: [...c.specs, { field: "", name: {}, desc: {}, subjects: [] }] })}>{t("admin.lyceums.addSpecialization")}</Btn>
      </fieldset>

      <fieldset className={box}>
        <legend className={legend}>{t("admin.lyceums.offerings")}</legend>
        {c.offerings.map((o, i) => (
          <div key={i} className="space-y-2 rounded-xl border border-line p-2">
            <div className="flex items-start gap-2">
              <div className="flex-1"><Localized label={t("admin.lyceums.offeringTitle")} value={o.title} onChange={(title) => set({ offerings: move(c.offerings, i, { ...o, title }) })} /></div>
              <RemoveBtn onClick={() => set({ offerings: move(c.offerings, i, null) })} />
            </div>
            <Localized area label={t("admin.lyceums.description")} value={o.desc} onChange={(desc) => set({ offerings: move(c.offerings, i, { ...o, desc }) })} />
            <Localized label={t("admin.lyceums.offeringTaughtBy")} value={o.by} onChange={(by) => set({ offerings: move(c.offerings, i, { ...o, by }) })} />
          </div>
        ))}
        <Btn onClick={() => set({ offerings: [...c.offerings, { title: {}, desc: {}, by: {} }] })}>{t("admin.lyceums.addOffering")}</Btn>
      </fieldset>
    </div>
  );
}
