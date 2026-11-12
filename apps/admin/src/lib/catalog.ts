"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, type components } from "@dtmai/api-client";
import { api } from "./api";
import { useToast } from "@dtmai/ui";
import { errMsg } from "./util";

type S = components["schemas"];
export type Subject = S["SubjectOut"];
export type SubjectIn = S["SubjectIn"];
export type Topic = S["TopicOut"];
export type TopicIn = S["TopicIn"];
export type QType = S["QuestionTypeOut"];
export type QTypeIn = S["QuestionTypeIn"];
export type QBase = S["QuestionBaseOut"];
export type QBaseIn = S["QuestionBaseIn"];
export type PathT = S["PathOut"];
export type UnitT = S["UnitOut"];
export type LessonT = S["LessonOut"];
export type LessonIn = S["LessonIn"];
export type Blueprint = S["BlueprintOut"];
export type BlueprintIn = S["BlueprintIn"];
export type Coverage = S["CoverageRow"];
export type Audit = S["AuditOut"];
export type Question = S["QuestionAdminOut"];
export type QuestionBody = S["QuestionBody"];
export type ReferenceSheet = S["ReferenceSheetAdminOut"];
export type ReferenceSheetIn = S["ReferenceSheetIn"];
export type LaunchGateRow = S["LaunchGateRow"];

const A = api.client;
const u = api.unwrap;

export const catalog = {
  subjects: {
    list: () => u(A.GET("/v1/admin/catalog/subjects")),
    create: (body: SubjectIn) => u(A.POST("/v1/admin/catalog/subjects", { body })),
    update: (id: string, body: Partial<SubjectIn>) => u(A.PATCH("/v1/admin/catalog/subjects/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/subjects/{item_id}", { params: { path: { item_id: id } } })),
  },
  reference: {
    /** 404 means "no sheet yet" -> null. */
    get: async (subject_id: string): Promise<ReferenceSheet | null> => {
      try { return await u(A.GET("/v1/admin/catalog/subjects/{subject_id}/reference", { params: { path: { subject_id } } })); }
      catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e; }
    },
    put: (subject_id: string, body: ReferenceSheetIn) => u(A.PUT("/v1/admin/catalog/subjects/{subject_id}/reference", { params: { path: { subject_id } }, body })),
    remove: (subject_id: string) => u(A.DELETE("/v1/admin/catalog/subjects/{subject_id}/reference", { params: { path: { subject_id } } })),
  },
  topics: {
    list: (subject_id: string) => u(A.GET("/v1/admin/catalog/topics", { params: { query: { subject_id } } })),
    create: (body: TopicIn) => u(A.POST("/v1/admin/catalog/topics", { body })),
    update: (id: string, body: Partial<TopicIn>) => u(A.PATCH("/v1/admin/catalog/topics/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/topics/{item_id}", { params: { path: { item_id: id } } })),
    reorder: (subject_id: string, ids: string[]) => u(A.POST("/v1/admin/catalog/topics/reorder", { params: { query: { subject_id } }, body: { ids } })),
  },
  types: {
    list: () => u(A.GET("/v1/admin/catalog/question-types")),
    create: (body: QTypeIn) => u(A.POST("/v1/admin/catalog/question-types", { body })),
    update: (id: string, body: Partial<QTypeIn>) => u(A.PATCH("/v1/admin/catalog/question-types/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/question-types/{item_id}", { params: { path: { item_id: id } } })),
  },
  bases: {
    list: (include_archived = false) => u(A.GET("/v1/admin/catalog/question-bases", { params: { query: { include_archived } } })),
    archive: (item_id: string) => u(A.POST("/v1/admin/catalog/question-bases/{item_id}/archive", { params: { path: { item_id } } })),
    unarchive: (item_id: string) => u(A.POST("/v1/admin/catalog/question-bases/{item_id}/unarchive", { params: { path: { item_id } } })),
    create: (body: QBaseIn) => u(A.POST("/v1/admin/catalog/question-bases", { body })),
    update: (id: string, body: Partial<QBaseIn>) => u(A.PATCH("/v1/admin/catalog/question-bases/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/question-bases/{item_id}", { params: { path: { item_id: id } } })),
  },
  paths: {
    list: (subject_id: string) => u(A.GET("/v1/admin/catalog/paths", { params: { query: { subject_id } } })),
    create: (body: S["PathIn"]) => u(A.POST("/v1/admin/catalog/paths", { body })),
    update: (id: string, body: Partial<S["PathIn"]>) => u(A.PATCH("/v1/admin/catalog/paths/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/paths/{item_id}", { params: { path: { item_id: id } } })),
    publish: (id: string) => u(A.POST("/v1/admin/catalog/paths/{item_id}/publish", { params: { path: { item_id: id } } })),
    unpublish: (id: string) => u(A.POST("/v1/admin/catalog/paths/{item_id}/unpublish", { params: { path: { item_id: id } } })),
  },
  units: {
    list: (path_id: string) => u(A.GET("/v1/admin/catalog/units", { params: { query: { path_id } } })),
    create: (body: S["UnitIn"]) => u(A.POST("/v1/admin/catalog/units", { body })),
    update: (id: string, body: Partial<S["UnitIn"]>) => u(A.PATCH("/v1/admin/catalog/units/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/units/{item_id}", { params: { path: { item_id: id } } })),
    reorder: (path_id: string, ids: string[]) => u(A.POST("/v1/admin/catalog/units/reorder", { params: { query: { path_id } }, body: { ids } })),
  },
  lessons: {
    list: (unit_id: string) => u(A.GET("/v1/admin/catalog/lessons", { params: { query: { unit_id } } })),
    create: (body: LessonIn) => u(A.POST("/v1/admin/catalog/lessons", { body })),
    update: (id: string, body: Partial<LessonIn>) => u(A.PATCH("/v1/admin/catalog/lessons/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/lessons/{item_id}", { params: { path: { item_id: id } } })),
    reorder: (unit_id: string, ids: string[]) => u(A.POST("/v1/admin/catalog/lessons/reorder", { params: { query: { unit_id } }, body: { ids } })),
  },
  blueprints: {
    list: () => u(A.GET("/v1/admin/catalog/blueprints")),
    create: (body: BlueprintIn) => u(A.POST("/v1/admin/catalog/blueprints", { body })),
    update: (id: string, body: Partial<BlueprintIn>) => u(A.PATCH("/v1/admin/catalog/blueprints/{item_id}", { params: { path: { item_id: id } }, body })),
    remove: (id: string) => u(A.DELETE("/v1/admin/catalog/blueprints/{item_id}", { params: { path: { item_id: id } } })),
    clone: (id: string) => u(A.POST("/v1/admin/catalog/blueprints/{item_id}/clone", { params: { path: { item_id: id } } })),
    publish: (id: string) => u(A.POST("/v1/admin/catalog/blueprints/{item_id}/publish", { params: { path: { item_id: id } } })),
  },
  launchGate: (subject_id: string) => u(A.GET("/v1/admin/catalog/launch-gate", { params: { query: { subject_id } } })),
  audit: (q: { entity?: string; entity_id?: string; limit?: number }) => u(A.GET("/v1/admin/catalog/audit-log", { params: { query: q } })),
};

export const qk = {
  subjects: ["subjects"], types: ["types"], bases: ["bases"], blueprints: ["blueprints"],
  reference: (s: string) => ["reference", s], topics: (s: string) => ["topics", s], paths: (s: string) => ["paths", s], units: (p: string) => ["units", p], lessons: (u: string) => ["lessons", u],
} as const;

export const useSubjects = () => useQuery({ queryKey: qk.subjects, queryFn: catalog.subjects.list, staleTime: 60_000 });
export const useTypes = () => useQuery({ queryKey: qk.types, queryFn: catalog.types.list, staleTime: 60_000 });
export const useBases = () => useQuery({ queryKey: qk.bases, queryFn: () => catalog.bases.list(), staleTime: 60_000 });
export const useTopics = (subjectId: string | undefined) =>
  useQuery({ queryKey: qk.topics(subjectId ?? ""), queryFn: () => catalog.topics.list(subjectId!), enabled: !!subjectId, staleTime: 60_000 });

let lastErr = { msg: "", at: 0 };
/** Mutation that toasts the outcome and invalidates the given query-key prefixes. */
export function useAct<A, R>(fn: (a: A) => Promise<R>, invalidate: readonly (readonly unknown[])[], ok?: string) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      for (const k of invalidate) void qc.invalidateQueries({ queryKey: k as unknown[] });
      if (ok) toast(ok, "success");
    },
    onError: (e) => {
      // One toast per distinct message per 4s so a failing burst (retries, bulk) never stacks.
      const msg = errMsg(e), now = Date.now();
      if (lastErr.msg === msg && now - lastErr.at < 4000) return;
      lastErr = { msg, at: now };
      toast(msg, "error");
    },
  });
}
