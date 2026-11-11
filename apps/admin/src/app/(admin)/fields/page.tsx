"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useSubjects } from "@/lib/catalog";
import { useAct } from "@/lib/catalog";
import { lyceums, type FieldOf } from "@/lib/lyceums";
import { nm } from "@/lib/util";
import { Badge, Btn, Input, PageHeader, Select } from "@/components/ui/controls";
import { DataTable } from "@/components/ui/table";

const KEY = ["lyceum-fields"];

export default function FieldsPage() {
  const fields = useQuery({ queryKey: KEY, queryFn: () => lyceums.fields() });
  const subjects = useSubjects();
  const [q, setQ] = useState("");
  const [draft, setDraft] = useState<{ code: string; ids: string[] } | null>(null);
  const save = useAct((a: { code: string; ids: string[] }) => lyceums.setFieldSubjects(a.code, a.ids), [KEY], "Mapping saved");
  const clear = useAct((code: string) => lyceums.clearFieldSubjects(code), [KEY], "Mapping cleared");
  const subjectName = new Map((subjects.data ?? []).map((s) => [s.id, nm(s.names)]));
  const needle = q.trim().toLowerCase();
  const rows = (fields.data ?? []).filter((f) => !needle || f.code.toLowerCase().includes(needle) || f.name.toLowerCase().includes(needle));

  const open = (f: FieldOf) => setDraft({ code: f.code, ids: [...f.subject_ids] });
  const move = (i: number, d: number) =>
    setDraft((cur) => {
      if (!cur) return cur;
      const ids = [...cur.ids];
      const j = i + d;
      if (j < 0 || j >= ids.length) return cur;
      [ids[i], ids[j]] = [ids[j]!, ids[i]!];
      return { ...cur, ids };
    });
  const addable = (subjects.data ?? []).filter((s) => !draft?.ids.includes(s.id));

  return (
    <>
      <PageHeader title="Fields of study" sub="Each edu.uz speciality maps to an ordered list of catalog subjects. Learners who pick a mapped field get these subjects automatically." />
      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        <Input placeholder="Search code or name" value={q} onChange={(e) => setQ(e.target.value)} />
        {draft && (
          <div className="space-y-3 rounded-xl border border-line bg-white p-4">
            <div className="font-extrabold">{draft.code} · {fields.data?.find((f) => f.code === draft.code)?.name}</div>
            <ol className="space-y-1">
              {draft.ids.map((id, i) => (
                <li key={id} className="flex items-center gap-2">
                  <span className="w-6 text-sm text-ink-soft">{i + 1}.</span>
                  <span className="flex-1">{subjectName.get(id) ?? id}</span>
                  <Btn disabled={i === 0} onClick={() => move(i, -1)} aria-label="Move up">↑</Btn>
                  <Btn disabled={i === draft.ids.length - 1} onClick={() => move(i, 1)} aria-label="Move down">↓</Btn>
                  <Btn onClick={() => setDraft({ ...draft, ids: draft.ids.filter((x) => x !== id) })}>Remove</Btn>
                </li>
              ))}
              {draft.ids.length === 0 && <li className="text-sm text-ink-soft">No subjects: saving clears the mapping and learners choose subjects themselves.</li>}
            </ol>
            <Select value="" onChange={(e) => e.target.value && setDraft({ ...draft, ids: [...draft.ids, e.target.value] })}>
              <option value="">Add subject…</option>
              {addable.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}
            </Select>
            <div className="flex gap-2">
              <Btn variant="primary" disabled={save.isPending} onClick={() => save.mutate(draft, { onSuccess: () => setDraft(null) })}>Save</Btn>
              <Btn onClick={() => setDraft(null)}>Cancel</Btn>
            </div>
          </div>
        )}
        <DataTable rows={rows} loading={fields.isLoading} error={fields.error} rowKey={(f) => f.code} empty="No fields yet. Import a lyceums year first."
          cols={[
            { key: "c", head: "Code", cell: (f) => f.code },
            { key: "n", head: "Field", cell: (f) => f.name },
            { key: "s", head: "Subjects", cell: (f) => f.mapped ? f.subject_ids.map((id) => subjectName.get(id) ?? id).join(", ") : <Badge tone="gray">Not mapped</Badge> },
            { key: "a", head: "", cell: (f) => (
              <div className="flex gap-2">
                <Btn onClick={() => open(f)}>Edit</Btn>
                {f.mapped && <Btn disabled={clear.isPending} onClick={() => clear.mutate(f.code)}>Clear</Btn>}
              </div>
            ) },
          ]} />
      </div>
    </>
  );
}
