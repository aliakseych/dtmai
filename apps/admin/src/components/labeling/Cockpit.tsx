"use client";
import { useT, useEnum } from "@/lib/i18n";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EmptyState, Icon, useToast } from "@dtmai/ui";
import { ApiError } from "@dtmai/api-client";
import { useSubjects } from "@/lib/catalog";
import { api } from "@/lib/api";
import { labeling, type LFilters, type QueueState, type Review } from "@/lib/labeling";
import { errMsg, nm } from "@/lib/util";
import { useAuth } from "@/lib/auth";
import { Badge, Btn, Input, Select, Spinner, Textarea } from "@/components/ui/controls";
import { Md } from "@/components/ui/markdown";
import { LangInput } from "@/components/ui/lang";
import { mediaUrl } from "@/lib/env";
import { QuestionBody, fmtAnswer } from "./answer";
import { TypedInput, answerFromDraft, draftFromAnswer, isTyped, sameAnswer, type Draft } from "./AnswerInput";
import { BulkDialog } from "./BulkDialog";

const BUFFER = 4;
const STATES: QueueState[] = ["auto_agreed", "escalated", "needs_human"];
type R = Record<string, unknown>;
type Action = "accept" | "edit" | "skip" | "flag";
/** decisionId is null until the background send lands; action "gone" = resolved elsewhere (nothing to undo). */
interface Done { decisionId: string | null; action: Action | "gone" }

const fetchPassage = (id: string) => api.unwrap(api.client.GET("/v1/admin/bank/passages/{passage_id}", { params: { path: { passage_id: id } } }));

export function Cockpit() {
  const t = useT();
  const toast = useToast();
  const qc = useQueryClient();
  const { isAdmin } = useAuth();
  const subjects = useSubjects();
  const [filters, setFilters] = useState<LFilters>({});
  const [items, setItems] = useState<Review[]>([]);
  const [idx, setIdx] = useState(0);
  const [empty, setEmpty] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [done, setDone] = useState<Record<string, Done>>({});
  const [picked, setPicked] = useState<string[]>([]);
  const [draft, setDraft] = useState<Draft>({});
  const [editJson, setEditJson] = useState<string | null>(null);
  const [flagging, setFlagging] = useState<string | null>(null);
  const [blind, setBlind] = useState(false);
  const [bulk, setBulk] = useState(false);
  const [session, setSession] = useState<{ t0: number; n: number; ms: number }>({ t0: 0, n: 0, ms: 0 });
  const [, tick] = useState(0);
  const filling = useRef(false);
  const shownAt = useRef(Date.now());
  const en = useEnum();
  const gen = useRef(0); // bumps on filter change so stale fills are dropped
  const doneRef = useRef<Record<string, Done>>({});
  const pending = useRef(new Map<string, Promise<void>>());

  const stats = useQuery({ queryKey: ["labeling-stats"], queryFn: () => labeling.stats(1), refetchInterval: 15_000 });
  const cur = items[idx];
  const curDone = cur ? done[cur.question.id] : undefined;

  const idxRef = useRef(0); idxRef.current = idx;
  const itemsRef = useRef<Review[]>([]); itemsRef.current = items;
  const filtersRef = useRef(filters); filtersRef.current = filters;
  const setDoneMap = useCallback((fn: (m: Record<string, Done>) => Record<string, Done>) => { doneRef.current = fn(doneRef.current); setDone(doneRef.current); }, []);

  // Prefetch: keep BUFFER undecided items claimed ahead of the cursor (and their passages cached).
  const lastFail = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const fill = useCallback(async () => {
    if (filling.current || empty || conflict || Date.now() - lastFail.current < 3000) return;
    filling.current = true;
    const g = gen.current;
    try {
      // Bounded: at most BUFFER claims per pass; the server is told what we already hold (`exclude`) so a
      // re-served item is a protocol violation and ends the pass instead of looping.
      for (let n = 0; n < BUFFER; n++) {
        if (!mounted.current || BUFFER - (itemsRef.current.length - idxRef.current) <= 0) break;
        let r: Review;
        try { r = await labeling.next(filtersRef.current, itemsRef.current.map((x) => x.question.id)); } catch (e) {
          if (g !== gen.current || !mounted.current) break;
          if (e instanceof ApiError && e.status === 404) setEmpty(true);
          else if (e instanceof ApiError && e.status === 409) setConflict(true);
          else { lastFail.current = Date.now(); toast(errMsg(e), "error"); }
          break;
        }
        if (g !== gen.current || !mounted.current) break;
        if (itemsRef.current.some((x) => x.question.id === r.question.id)) { lastFail.current = Date.now(); break; }
        const pid = r.question.passage_id;
        if (pid) void qc.prefetchQuery({ queryKey: ["labeling-passage", pid], queryFn: () => fetchPassage(pid), staleTime: 600_000 });
        itemsRef.current = [...itemsRef.current, r]; setItems(itemsRef.current);
      }
    } finally { filling.current = false; }
  }, [empty, conflict, toast, qc]);
  useEffect(() => { void fill(); }, [fill, idx, items.length, filters]);
  useEffect(() => { const t = setInterval(() => tick((n) => n + 1), 5000); return () => clearInterval(t); }, []);
  // Lease conflict: retry on its own every 20s as other labelers' leases expire.
  useEffect(() => { if (!conflict) return; const t = setTimeout(() => setConflict(false), 20_000); return () => clearTimeout(t); }, [conflict]);

  /** Releases leases of buffered, undecided items (skip clears the claim). Audit samples hold no lease. */
  const releaseBuffer = useCallback(() => {
    for (const it of itemsRef.current) {
      if (doneRef.current[it.question.id] || it.audit_sample_id) continue;
      void labeling.decide(it.question.id, { action: "skip", reason: "released", time_ms: 0 }).catch(() => {});
    }
  }, []);
  useEffect(() => releaseBuffer, [releaseBuffer]);

  const resetQueue = (f: LFilters) => {
    releaseBuffer();
    gen.current++; filling.current = false; pending.current.clear();
    itemsRef.current = []; idxRef.current = 0; doneRef.current = {};
    setFilters(f); setItems([]); setIdx(0); setEmpty(false); setConflict(false); setDone({});
  };

  const kind = cur?.question.kind ?? "";
  const typed = isTyped(kind);
  // Blind mode: never prefill from the model's suggestion.
  const suggested = !blind ? cur?.suggested ?? null : null;
  const sugIds = suggested ? ((suggested.choice ? [String(suggested.choice)] : (suggested.choices as string[] | undefined)) ?? []) : [];
  const choiceKind = kind === "single_choice" || kind === "multi_choice";

  useEffect(() => { shownAt.current = Date.now(); setPicked([]); setEditJson(null); setFlagging(null); }, [cur?.question.id]);
  useEffect(() => { setDraft(draftFromAnswer(kind, suggested)); }, [cur?.question.id, blind]); // eslint-disable-line react-hooks/exhaustive-deps

  const pick = useCallback((id: string) => setPicked((p) => (kind === "multi_choice" ? (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]) : [id])), [kind]);

  // The pick/draft the labeler has entered, as a response.
  const entered = (): R | null => {
    if (kind === "single_choice") return picked[0] ? { choice: picked[0] } : null;
    if (kind === "multi_choice") return picked.length ? { choices: picked } : null;
    return typed && cur ? answerFromDraft(kind, cur.question.payload, draft) : null;
  };

  /** Optimistic: record + advance now, send in the background, roll back on failure. */
  const decide = useCallback((action: Action, response?: R, reason?: string) => {
    if (!cur || doneRef.current[cur.question.id]) return;
    const item = cur, qid = item.question.id, i = idxRef.current;
    const ms = Date.now() - shownAt.current;
    setDoneMap((m) => ({ ...m, [qid]: { decisionId: null, action } }));
    if (action !== "skip") setSession((s) => ({ t0: s.t0 || Date.now() - ms, n: s.n + 1, ms: s.ms + ms }));
    setIdx(i + 1);
    const g = gen.current;
    const p = labeling.decide(qid, { action, response, reason, time_ms: ms, audit_sample_id: item.audit_sample_id })
      .then((d) => { if (g === gen.current) setDoneMap((m) => (m[qid] ? { ...m, [qid]: { ...m[qid], decisionId: d.id } } : m)); })
      .catch((e) => {
        if (g !== gen.current) return;
        if (action !== "skip") setSession((s) => ({ ...s, n: Math.max(0, s.n - 1), ms: Math.max(0, s.ms - ms) }));
        if (e instanceof ApiError && e.status === 409) {
          setDoneMap((m) => ({ ...m, [qid]: { decisionId: null, action: "gone" } }));
          toast(t("admin.labeling.alreadyResolvedBySomeone"), "info");
          return;
        }
        setDoneMap((m) => { const n = { ...m }; delete n[qid]; return n; });
        setIdx((x) => Math.min(x, itemsRef.current.findIndex((y) => y.question.id === qid)));
        toast(t("admin.labeling.notSaved", { err: errMsg(e) }), "error");
      })
      .finally(() => { pending.current.delete(qid); });
    pending.current.set(qid, p);
  }, [cur, toast, setDoneMap]);

  const confirm = useCallback(() => {
    if (!cur) return;
    if (editJson !== null) {
      try { decide("edit", JSON.parse(editJson) as R); } catch { toast(t("admin.labeling.answerJsonIsInvalid"), "error"); }
      return;
    }
    const a = entered();
    if (a) return decide(suggested && sameAnswer(kind, a, suggested) ? "accept" : "edit", a);
    if (typed) return toast(t("admin.labeling.answerIsIncompleteOr"), "info");
    if (suggested) return decide("accept");
    toast(blind ? t("admin.labeling.blindPickFirst") : t("admin.labeling.noSuggestion"), "info");
  }, [cur, editJson, picked, draft, blind, decide, toast]); // eslint-disable-line react-hooks/exhaustive-deps

  const startEdit = () => {
    if (!cur || doneRef.current[cur.question.id]) return;
    if (typed) return void document.querySelector<HTMLInputElement>("[data-answer]")?.focus();
    setEditJson(JSON.stringify(suggested ?? entered() ?? {}, null, 2));
  };

  const undo = useCallback(async () => {
    // Undo the most recent decided item at or before the cursor.
    for (let i = Math.min(idxRef.current, itemsRef.current.length - 1); i >= 0; i--) {
      const qid = itemsRef.current[i].question.id;
      if (!doneRef.current[qid]) continue;
      await pending.current.get(qid);
      const d = doneRef.current[qid];
      if (!d || d.action === "gone" || !d.decisionId) continue;
      try {
        // A skip has no state to revert server-side (it only hides the item from this queue): just return to it.
        if (d.action !== "skip") await labeling.undo(d.decisionId);
        setDoneMap((m) => { const n = { ...m }; delete n[qid]; return n; });
        setIdx(i);
        setSession((s) => ({ ...s, n: Math.max(0, s.n - (d.action === "skip" ? 0 : 1)) }));
        toast(t("admin.labeling.undone"), "success");
      } catch (e) { toast(errMsg(e), "error"); }
      return;
    }
  }, [toast, setDoneMap]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      const typing = t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT";
      if (flagging !== null && e.key === "Enter") { e.preventDefault(); decide("flag", undefined, flagging || "flagged"); return; }
      if (e.key === "Escape") { setEditJson(null); setFlagging(null); if (typing) t.blur(); return; }
      if (typing) {
        if (e.key !== "Enter" || e.shiftKey) return;
        if (e.metaKey || e.ctrlKey) return confirm();
        if (t.dataset.answer) {
          e.preventDefault();
          // Enter walks to the next empty required input, then confirms.
          const next = Array.from(document.querySelectorAll<HTMLInputElement>('[data-answer="req"]')).find((el) => el !== t && !el.value.trim());
          if (next) next.focus(); else confirm();
        }
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key.toLowerCase();
      const opts = cur?.question.payload.options as { id: string }[] | undefined;
      if (/^[1-9]$/.test(k) && choiceKind) { const o = opts?.[Number(k) - 1]; if (o) pick(o.id); }
      else if (/^[a-d]$/.test(k) && choiceKind) { const o = opts?.[k.charCodeAt(0) - 97]; if (o) pick(o.id); }
      else if (e.key === "Enter") { e.preventDefault(); confirm(); }
      else if (k === "s") decide("skip");
      else if (k === "f") { e.preventDefault(); setFlagging(""); }
      else if (k === "e") { e.preventDefault(); startEdit(); }
      else if (k === "h") setBlind((b) => !b);
      else if (k === "z") void undo();
      else if (k === "j") setIdx((i) => Math.min(i + 1, Math.max(0, itemsRef.current.length - 1)));
      else if (k === "k") setIdx((i) => Math.max(0, i - 1));
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [cur, choiceKind, flagging, confirm, decide, undo, pick]); // eslint-disable-line react-hooks/exhaustive-deps

  const mins = session.t0 ? Math.max((Date.now() - session.t0) / 60000, 1 / 6) : 0;
  const rate = session.n ? (session.n / mins) : 0;
  const q = cur?.question;
  const conf = cur?.confidence;
  const queueDepth = useMemo(() => Object.entries(stats.data?.queue_depth ?? {}), [stats.data]);
  const passage = useQuery({ queryKey: ["labeling-passage", q?.passage_id], queryFn: () => fetchPassage(q!.passage_id!), enabled: !!q?.passage_id, staleTime: 600_000 });

  return (
    <div className="flex h-screen flex-col bg-snow text-ink">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line bg-white px-3 py-2 text-sm sm:px-4">
        <Link href="/questions/" className="tap font-extrabold text-blue-deep">{t("admin.labeling.admin")}</Link>
        <h1 className="text-base">{t("admin.labeling.labeling")}</h1>
        <Select className="w-full sm:w-36" value={filters.subject_id ?? ""} onChange={(e) => resetQueue({ ...filters, subject_id: e.target.value || undefined })}><option value="">{t("admin.labeling.allSubjects")}</option>{subjects.data?.map((s) => <option key={s.id} value={s.id}>{nm(s.names)}</option>)}</Select>
        <Select className="w-full sm:w-32" value={filters.state ?? ""} onChange={(e) => resetQueue({ ...filters, state: (e.target.value || undefined) as QueueState | undefined })}><option value="">{t("admin.labeling.allStates")}</option>{STATES.map((s) => <option key={s} value={s}>{en("state", s)}</option>)}</Select>
        <div className="w-full sm:w-24"><LangInput value={filters.language ?? ""} onChange={(v) => resetQueue({ ...filters, language: v || undefined })} /></div>
        <label className="flex min-h-11 items-center gap-1.5"><input type="checkbox" className="accent-blue" checked={blind} onChange={(e) => setBlind(e.target.checked)} />{t("admin.labeling.blind")} <kbd className="hidden md:inline text-xs opacity-60">H</kbd></label>
        <div className="flex min-w-0 flex-wrap items-center gap-2 sm:ml-auto sm:gap-3">
          {queueDepth.map(([k, v]) => <Badge key={k} tone={k === "needs_human" ? "red" : k === "escalated" ? "orange" : "green"}>{en("state", k)} {v}</Badge>)}
          <span title={t("admin.labeling.thisSession")} className="font-extrabold">{t("admin.labeling.sessionStat", { n: session.n, rate: rate.toFixed(1) })}{session.n ? t("admin.labeling.avg", { s: (session.ms / session.n / 1000).toFixed(1) }) : ""}</span>
          {stats.data?.audit.rate != null && <Badge tone={stats.data.audit.rate >= 0.95 ? "green" : "red"}>{t("admin.labeling.auditBadge", { pct: (stats.data.audit.rate * 100).toFixed(0), m: stats.data.audit.matched, a: stats.data.audit.audited })}</Badge>}
          {isAdmin && <Btn onClick={() => setBulk(true)}>{t("admin.labeling.bulkApprove")}</Btn>}
        </div>
      </header>

      <main className="mx-auto grid min-h-0 w-full max-w-6xl flex-1 grid-cols-1 gap-6 overflow-y-auto p-3 sm:p-6 lg:grid-cols-[1fr_22rem]">
        {!q ? (
          <div className="col-span-2 grid place-items-center">
            {conflict ? (
              <EmptyState compact title={<span className="inline-flex items-center gap-2"><Icon name="lock" size={20} />{t("admin.labeling.leaseConflictTheRemaining")}</span>} body={t("admin.labeling.retryingAutomaticallyEvery20s")} action={<Btn onClick={() => setConflict(false)}>{t("admin.labeling.retryNow")}</Btn>} />
            ) : empty ? <EmptyState compact title={<span className="inline-flex items-center gap-2"><Icon name="check" size={20} />{t("admin.labeling.queueIsEmptyFor")}</span>} /> : <Spinner />}
          </div>
        ) : (
          <>
            <section className="space-y-4">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Badge tone="blue">{en("kind", q.kind)}</Badge><Badge>{q.language}</Badge>
                <Badge tone={cur.state === "needs_human" ? "red" : cur.state === "escalated" ? "orange" : "green"}>{en("state", cur.state)}</Badge>
                {cur.audit_sample_id && <Badge tone="gold">{t("admin.labeling.auditSample")}</Badge>}
                {curDone && <Badge tone="gray">{t("admin.labeling.decided", { action: curDone.action })}</Badge>}
                <span className="ml-auto text-ink-soft">{t("admin.labeling.navHint", { i: idx + 1, n: items.length })}</span>
              </div>
              {passage.data && (
                <div className="max-h-[40vh] overflow-y-auto rounded-2xl border-2 border-blue bg-blue-soft p-5 text-base">
                  {passage.data.title && <h3 className="mb-2 font-extrabold">{passage.data.title}</h3>}
                  <Md text={passage.data.text} />
                </div>
              )}
              {q.passage_id && !passage.data && <div className="rounded-2xl border-2 border-line bg-white p-4 text-sm text-ink-soft">{passage.isError ? t("admin.labeling.passageFailedToLoad") : t("admin.labeling.loadingPassage")}</div>}
              <div className="rounded-2xl border-2 border-line bg-white p-5 text-lg"><Md text={q.stem} />
                {q.media.map((m, i) => { const k = (m as { key?: string }).key; return k ? <img key={i} alt="" src={mediaUrl(k)} className="mt-3 max-h-72 rounded-xl" /> : null; })}</div>
              <QuestionBody kind={q.kind} payload={q.payload} picked={picked} suggested={sugIds} onPick={pick} />
              {typed && !curDone && editJson === null && <TypedInput key={q.id} kind={q.kind} payload={q.payload} draft={draft} onChange={setDraft} />}
              {editJson !== null && (
                <div className="space-y-1"><label className="text-xs font-extrabold uppercase text-ink-soft">{t("admin.labeling.answerJsonCtrlEnter")}</label>
                  <Textarea autoFocus rows={6} className="font-mono text-xs" value={editJson} onChange={(e) => setEditJson(e.target.value)} /></div>
              )}
              {flagging !== null && (
                <div className="flex gap-2"><Input autoFocus placeholder={t("admin.labeling.flagReasonEnterTo")} value={flagging} onChange={(e) => setFlagging(e.target.value)} maxLength={200} /><Btn variant="danger" onClick={() => decide("flag", undefined, flagging || "flagged")}>{t("admin.labeling.flag2")}</Btn></div>
              )}
            </section>
            <aside className="space-y-4">
              <div className="rounded-xl border border-line bg-white p-4">
                <h3 className="mb-2 text-xs font-extrabold uppercase text-ink-soft">{t("admin.labeling.modelConsensus")}</h3>
                {blind ? <p className="text-sm text-ink-soft">{t("admin.labeling.hiddenBlindMode")} <kbd>H</kbd> {t("admin.labeling.toToggleChooseIndependently")}</p> : (
                  <>
                    <div className="flex items-center gap-2"><span className="text-2xl font-extrabold">{fmtAnswer(q.kind, q.payload, cur.suggested)}</span>
                      {conf != null && <Badge tone={conf >= 0.9 ? "green" : conf >= 0.6 ? "gold" : "red"}>{t("admin.labeling.agreePct", { pct: Math.round(conf * 100) })}</Badge>}</div>
                    <p className="mt-2 text-sm text-ink-soft">{en("consensus", cur.reason)}</p>
                  </>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Btn variant="primary" disabled={!!curDone} onClick={confirm}>{entered() && !(suggested && sameAnswer(kind, entered(), suggested)) || editJson !== null ? t("admin.labeling.submitAnswer") : t("admin.labeling.accept")} <kbd className="hidden md:inline ml-1 opacity-70">Enter</kbd></Btn>
                <Btn disabled={!!curDone} onClick={() => decide("skip")}>{t("admin.labeling.skip2")} <kbd className="hidden md:inline opacity-60">S</kbd></Btn>
                <Btn variant="danger" disabled={!!curDone} onClick={() => setFlagging("")}>{t("admin.labeling.flag2")} <kbd className="hidden md:inline opacity-60">F</kbd></Btn>
                <Btn disabled={!!curDone} onClick={startEdit}>{t("admin.common.edit")} <kbd className="hidden md:inline opacity-60">E</kbd></Btn>
                <Btn className="col-span-2" onClick={() => void undo()}>{t("admin.labeling.undo2")} <kbd className="hidden md:inline opacity-60">Z</kbd></Btn>
              </div>
              <p className="hidden text-xs text-ink-soft md:block"><kbd>1–9</kbd>/<kbd>A–D</kbd> {t("admin.labeling.pick")} <kbd>Enter</kbd> {t("admin.labeling.acceptSubmitTypedKinds")} <kbd>Enter</kbd> {t("admin.labeling.walksTheFields")} <kbd>S</kbd> {t("admin.labeling.skip")} <kbd>F</kbd> {t("admin.labeling.flag")} <kbd>E</kbd> {t("admin.labeling.edit")} <kbd>H</kbd> {t("admin.labeling.blindOnOff")} <kbd>Z</kbd> {t("admin.labeling.undo")} <kbd>J</kbd>/<kbd>K</kbd> {t("admin.labeling.nextPrev")} <kbd>{t("admin.labeling.esc")}</kbd> {t("admin.labeling.leaveField", { n: Math.max(0, items.length - idx - 1) })}</p>
            </aside>
          </>
        )}
      </main>
      {bulk && <BulkDialog filters={filters} onClose={() => setBulk(false)} />}
    </div>
  );
}
