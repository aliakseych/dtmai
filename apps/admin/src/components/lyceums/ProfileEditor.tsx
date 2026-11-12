"use client";
import { useT } from "@/lib/i18n";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Icon, useToast } from "@dtmai/ui";
import { lyceums, type DormitoryStatus, type LyceumPatch, type LyceumRow } from "@/lib/lyceums";
import { useAct } from "@/lib/catalog";
import { uploadMedia } from "@/lib/media";
import { mediaUrl } from "@/lib/env";
import { errMsg, LOCALE_LIST, nm } from "@/lib/util";
import { Btn, Check, FileBtn, ErrorBox, Field, Input, Select, Spinner, Textarea } from "@/components/ui/controls";
import { CampusEditor, campusForm, campusPatch, type CampusForm } from "./CampusEditor";
import { Drawer } from "@/components/ui/overlay";

interface Form {
  logo: string; campus: string; gallery: string[];
  desc: Record<string, string>; courses: string[];
  university: string; city: string; website: string;
  phone: string; telegram: string; email: string; verified: boolean;
  dormStatus: DormitoryStatus; dormDesc: Record<string, string>;
  extra: CampusForm;
}

const DORM: DormitoryStatus[] = ["unknown", "available", "limited", "none"];

const orNull = (s: string) => (s.trim() ? s.trim() : null);

export function ImageSlot({ label, value, onChange }: { label: string; value: string; onChange: (key: string) => void }) {
  const t = useT();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const pick = async (f?: File, input?: HTMLInputElement) => {
    if (!f) return;
    setBusy(true);
    try { onChange((await uploadMedia(f)).key); } catch (e) { if (input) input.value = ""; toast(errMsg(e), "error"); } finally { setBusy(false); }
  };
  return (
    <Field label={label}>
      <div className="flex items-center gap-2">
        {value ? <img src={mediaUrl(value)} alt="" className="size-14 rounded-xl border border-line object-cover" /> : <div className="size-14 rounded-xl border border-dashed border-line" />}
        <FileBtn accept="image/*" disabled={busy} onFiles={(f, i) => void pick(f?.[0], i)} />
        {busy && <Spinner />}
        {value && <Btn variant="ghost" onClick={() => onChange("")}>{t("admin.common.remove")}</Btn>}
      </div>
    </Field>
  );
}

function Gallery({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const t = useT();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const add = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    try {
      const keys: string[] = [];
      for (const f of Array.from(files)) keys.push((await uploadMedia(f)).key);
      onChange([...value, ...keys]);
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  };
  return (
    <Field label={t("admin.lyceums.gallery")}>
      <div className="flex flex-wrap items-center gap-2">
        {value.map((k, i) => (
          <div key={k + i} className="relative">
            <img src={mediaUrl(k)} alt="" className="size-20 rounded-xl border border-line object-cover" />
            <button type="button" aria-label={t("admin.lyceums.removeImage")} onClick={() => onChange(value.filter((_, j) => j !== i))} className="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-red text-white"><Icon name="close" size={16} /></button>
          </div>
        ))}
        <FileBtn accept="image/*" multiple disabled={busy} onFiles={(f, i) => { void add(f); i.value = ""; }} />
        {busy && <Spinner />}
      </div>
    </Field>
  );
}

function Tags({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const t = useT();
  const [draft, setDraft] = useState("");
  const add = () => {
    const v = draft.trim();
    if (v && !value.includes(v)) onChange([...value, v]);
    setDraft("");
  };
  return (
    <Field label={t("admin.lyceums.courses")} hint={t("admin.lyceums.pressEnterToAdd")}>
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-line p-1.5">
        {value.map((c) => (
          <span key={c} className="inline-flex items-center gap-1 rounded bg-blue-soft px-1.5 py-0.5 text-xs font-bold">
            {c}
            <button type="button" aria-label={t("admin.lyceums.removeItem", { item: c })} onClick={() => onChange(value.filter((x) => x !== c))}><Icon name="close" size={16} /></button>
          </span>
        ))}
        <input value={draft} onChange={(e) => setDraft(e.target.value)} onBlur={add}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          className="min-w-32 flex-1 text-sm outline-none" placeholder={t("admin.lyceums.addCourse")} />
      </div>
    </Field>
  );
}

export function ProfileEditor({ lyceum, onClose }: { lyceum: LyceumRow | null; onClose: () => void }) {
  const t = useT();
  const toast = useToast();
  const detail = useQuery({ queryKey: ["lyceum-detail", lyceum?.id], queryFn: () => lyceums.detail(lyceum!.id), enabled: !!lyceum });
  const cities = useQuery({ queryKey: ["cities"], queryFn: lyceums.cities });
  const [f, setF] = useState<Form | null>(null);
  useEffect(() => {
    const p = detail.data?.profile;
    if (!p) return;
    setF({
      logo: p.logo_url ?? "", campus: p.campus_photo_url ?? "", gallery: p.gallery_urls, desc: { ...p.description },
      courses: p.courses, university: p.university_name ?? "", city: p.city ?? "", website: p.website ?? "",
      phone: p.contacts.phone ?? "", telegram: p.contacts.telegram ?? "", email: p.contacts.email ?? "", verified: p.verified_rep,
      dormStatus: p.dormitory_status, dormDesc: { ...p.dormitory_description }, extra: campusForm(p),
    });
  }, [detail.data]);
  const save = useAct((a: { id: string; body: LyceumPatch }) => lyceums.patch(a.id, a.body), [["lyceum-detail"]], t("admin.common.profileSaved"));
  const set = (p: Partial<Form>) => setF((x) => (x ? { ...x, ...p } : x));
  const submit = () => {
    if (!lyceum || !f) return;
    if (f.extra.buildings.some((b) => b.plans.some((p) => !p.image))) { toast(t("admin.lyceums.floorPlanImageRequired"), "error"); return; }
    save.mutate({
      id: lyceum.id,
      body: {
        logo_url: orNull(f.logo), campus_photo_url: orNull(f.campus), gallery_urls: f.gallery, courses: f.courses,
        description: Object.fromEntries(Object.entries(f.desc).filter(([, v]) => v.trim())),
        university_name: orNull(f.university), city: orNull(f.city), website: orNull(f.website),
        contacts: { phone: orNull(f.phone), telegram: orNull(f.telegram), email: orNull(f.email) },
        verified_rep: f.verified,
        ...campusPatch(f.extra),
        dormitory_status: f.dormStatus,
        dormitory_description: Object.fromEntries(Object.entries(f.dormDesc).filter(([, v]) => v.trim())),
      },
    }, { onSuccess: onClose });
  };
  return (
    <Drawer open={!!lyceum} onClose={onClose} title={lyceum ? t("admin.lyceums.profileTitle", { name: nm(lyceum.names) }) : ""} width="max-w-2xl"
      footer={<><Btn onClick={onClose}>{t("admin.common.cancel")}</Btn><Btn variant="primary" disabled={!f || save.isPending} onClick={submit}>{t("admin.common.save")}</Btn></>}>
      {detail.error ? <ErrorBox error={detail.error} /> : !f ? <div className="grid place-items-center p-8"><Spinner /></div> : (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <ImageSlot label={t("admin.lyceums.logo")} value={f.logo} onChange={(logo) => set({ logo })} />
            <ImageSlot label={t("admin.lyceums.campusPhoto")} value={f.campus} onChange={(campus) => set({ campus })} />
          </div>
          <Gallery value={f.gallery} onChange={(gallery) => set({ gallery })} />
          <fieldset className="space-y-2 rounded-xl border border-line p-2">
            <legend className="px-1 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{t("admin.lyceums.description")}</legend>
            {LOCALE_LIST.map((l) => (
              <Field key={l} label={l}><Textarea className="font-sans" value={f.desc[l] ?? ""} onChange={(e) => set({ desc: { ...f.desc, [l]: e.target.value } })} /></Field>
            ))}
          </fieldset>
          <Tags value={f.courses} onChange={(courses) => set({ courses })} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label={t("admin.lyceums.universityName")} hint={t("admin.lyceums.enteredManually")}><Input value={f.university} onChange={(e) => set({ university: e.target.value })} /></Field>
            <Field label={t("admin.lyceums.city")}>
              <Select value={f.city} onChange={(e) => set({ city: e.target.value })}>
                <option value="">{t("admin.lyceums.anyNone")}</option>
                {(cities.data ?? []).map((c) => <option key={c.code} value={c.code}>{nm(c.names)}</option>)}
              </Select>
            </Field>
            <Field label={t("admin.lyceums.website")} className="sm:col-span-2"><Input type="url" value={f.website} onChange={(e) => set({ website: e.target.value })} placeholder={t("admin.lyceums.https")} /></Field>
            <Field label={t("admin.lyceums.phone")}><Input value={f.phone} onChange={(e) => set({ phone: e.target.value })} /></Field>
            <Field label={t("admin.lyceums.telegram")}><Input value={f.telegram} onChange={(e) => set({ telegram: e.target.value })} /></Field>
            <Field label={t("admin.common.email")} className="sm:col-span-2"><Input type="email" value={f.email} onChange={(e) => set({ email: e.target.value })} /></Field>
          </div>
          <fieldset className="space-y-2 rounded-xl border border-line p-2">
            <legend className="px-1 text-xs font-extrabold uppercase tracking-wide text-ink-soft">{t("admin.lyceums.dormitory")}</legend>
            <Field label={t("admin.common.status")}>
              <Select value={f.dormStatus} onChange={(e) => set({ dormStatus: e.target.value as DormitoryStatus })}>
                {DORM.map((d) => <option key={d} value={d}>{t(`lyceums.dorm.${d}`)}</option>)}
              </Select>
            </Field>
            {LOCALE_LIST.map((l) => (
              <Field key={l} label={l}><Textarea className="font-sans" value={f.dormDesc[l] ?? ""} onChange={(e) => set({ dormDesc: { ...f.dormDesc, [l]: e.target.value } })} /></Field>
            ))}
          </fieldset>
          <CampusEditor value={f.extra} onChange={(extra) => set({ extra })} />
          <Check checked={f.verified} onChange={(verified) => set({ verified })} label={t("admin.lyceums.verifiedRepresentativeBadge")} />
        </div>
      )}
    </Drawer>
  );
}
