"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";
import type { Kind } from "./util";

type S = components["schemas"];
export type QuestionPatch = S["QuestionPatch"];
export type Status = S["StatusIn"]["status"];
export interface QFilters {
  subject_id?: string; topic_id?: string; type_id?: string; language?: string; status?: Status;
  source_id?: string; kind?: string; q?: string; reported?: boolean; limit: number; offset: number;
}
const A = api.client;
const u = api.unwrap;
const clean = <T extends object>(o: T) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== "" && v !== undefined && v !== false)) as T;

export const bank = {
  list: (f: QFilters) => u(A.GET("/v1/admin/bank/questions", { params: { query: clean(f) } })),
  get: (id: string) => u(A.GET("/v1/admin/bank/questions/{question_id}", { params: { path: { question_id: id } } })),
  create: (body: S["QuestionBody"]) => u(A.POST("/v1/admin/bank/questions", { body })),
  patch: (id: string, body: QuestionPatch) => u(A.PATCH("/v1/admin/bank/questions/{question_id}", { params: { path: { question_id: id } }, body })),
  setStatus: (id: string, status: Status, reason: string) => u(A.POST("/v1/admin/bank/questions/{question_id}/status", { params: { path: { question_id: id } }, body: { status, reason } })),
  bulkStatus: (ids: string[], status: Status, reason: string) => u(A.POST("/v1/admin/bank/questions/bulk-status", { body: { ids, status, reason } })),
  import: (items: Record<string, unknown>[]) => u(A.POST("/v1/admin/bank/questions/import", { body: { items } })),
  explanation: (id: string, locale: string) => u(A.GET("/v1/admin/bank/questions/{question_id}/explanations/{locale}", { params: { path: { question_id: id, locale } } })),
  putExplanation: (id: string, locale: string, text: string) => u(A.PUT("/v1/admin/bank/questions/{question_id}/explanations/{locale}", { params: { path: { question_id: id, locale } }, body: { text, model: "human" } })),
  passages: () => u(A.GET("/v1/admin/bank/passages")),
};

/** Kind-specific editor state <-> API payload/answer. */
export interface Opt { id: string; text: string; media?: string }
export interface Draft {
  kind: Kind;
  options: Opt[]; correct: string[];
  value: string; tolerance: string; unit: string;
  accepted: string; caseSensitive: boolean;
  left: Opt[]; right: Opt[]; pairs: Record<string, string>;
  items: Opt[];
  childIds: string;
}
export const emptyDraft = (kind: Kind): Draft => ({
  kind, options: [{ id: "a", text: "" }, { id: "b", text: "" }, { id: "c", text: "" }, { id: "d", text: "" }], correct: [],
  value: "", tolerance: "", unit: "", accepted: "", caseSensitive: false,
  left: [{ id: "l1", text: "" }, { id: "l2", text: "" }], right: [{ id: "r1", text: "" }, { id: "r2", text: "" }], pairs: {},
  items: [{ id: "i1", text: "" }, { id: "i2", text: "" }], childIds: "",
});

type R = Record<string, unknown>;
const arr = (v: unknown): R[] => (Array.isArray(v) ? (v as R[]) : []);
const toOpts = (v: unknown): Opt[] => arr(v).map((o) => ({ id: String(o.id ?? ""), text: String(o.text ?? ""), media: typeof o.media === "string" ? o.media : undefined }));
const fromOpts = (o: Opt[]) => o.map((x) => ({ id: x.id, text: x.text, ...(x.media ? { media: x.media } : {}) }));

export function draftFrom(kind: Kind, payload: R | undefined, answer: R | undefined): Draft {
  const d = emptyDraft(kind);
  const p = payload ?? {}, a = answer ?? {};
  switch (kind) {
    case "single_choice": return { ...d, options: toOpts(p.options), correct: a.choice ? [String(a.choice)] : [] };
    case "multi_choice": return { ...d, options: toOpts(p.options), correct: Array.isArray(a.choices) ? a.choices.map(String) : [] };
    case "numeric": return { ...d, value: a.value == null ? "" : String(a.value), tolerance: a.tolerance == null ? "" : String(a.tolerance), unit: String(p.unit ?? "") };
    case "short_text": return { ...d, accepted: Array.isArray(a.accepted) ? a.accepted.join("\n") : "", caseSensitive: !!a.case_sensitive };
    case "matching": return { ...d, left: toOpts(p.left), right: toOpts(p.right), pairs: (a.pairs as Record<string, string>) ?? {} };
    case "ordering": {
      const items = toOpts(p.items), order = Array.isArray(a.order) ? a.order.map(String) : [];
      return { ...d, items: order.length ? order.map((id) => items.find((i) => i.id === id)).filter((x): x is Opt => !!x).concat(items.filter((i) => !order.includes(i.id))) : items };
    }
    case "passage_group": return { ...d, childIds: Array.isArray(p.child_ids) ? p.child_ids.join("\n") : "" };
  }
}

export function draftTo(d: Draft): { payload: R; answer: R } {
  switch (d.kind) {
    case "single_choice": return { payload: { options: fromOpts(d.options) }, answer: { choice: d.correct[0] } };
    case "multi_choice": return { payload: { options: fromOpts(d.options) }, answer: { choices: d.correct } };
    case "numeric": return { payload: d.unit ? { unit: d.unit } : {}, answer: { value: Number(d.value), ...(d.tolerance ? { tolerance: Number(d.tolerance) } : {}) } };
    case "short_text": return { payload: {}, answer: { accepted: d.accepted.split("\n").map((s) => s.trim()).filter(Boolean), case_sensitive: d.caseSensitive } };
    case "matching": return { payload: { left: fromOpts(d.left), right: fromOpts(d.right) }, answer: { pairs: d.pairs } };
    case "ordering": return { payload: { items: fromOpts(d.items) }, answer: { order: d.items.map((i) => i.id) } };
    case "passage_group": return { payload: { child_ids: d.childIds.split(/[\s,]+/).filter(Boolean) }, answer: {} };
  }
}

/** Client-side validation mirroring the server's per-kind rules; returns an i18n error key or null. */
export function validateDraft(d: Draft): string | null {
  const ids = (o: Opt[]) => new Set(o.map((x) => x.id)).size === o.length && o.every((x) => x.id.trim());
  switch (d.kind) {
    case "single_choice": return d.options.length < 2 ? "admin.validate.optionsMin" : !ids(d.options) ? "admin.validate.optionIds" : d.correct.length !== 1 ? "admin.validate.pickOne" : null;
    case "multi_choice": return d.options.length < 2 ? "admin.validate.optionsMin" : !ids(d.options) ? "admin.validate.optionIds" : d.correct.length < 1 ? "admin.validate.pickAtLeastOne" : null;
    case "numeric": return d.value.trim() === "" || Number.isNaN(Number(d.value)) ? "admin.validate.numericRequired" : null;
    case "short_text": return d.accepted.trim() ? null : "admin.validate.acceptedRequired";
    case "matching": return !ids(d.left) || !ids(d.right) ? "admin.validate.pairIds" : d.left.some((l) => !d.pairs[l.id]) ? "admin.validate.needMatch" : null;
    case "ordering": return d.items.length < 2 ? "admin.validate.itemsMin" : ids(d.items) ? null : "admin.validate.itemIds";
    case "passage_group": return d.childIds.trim() ? null : "admin.validate.childIds";
  }
}
