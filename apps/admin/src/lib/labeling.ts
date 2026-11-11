"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Review = S["app__interfaces__http__v1__labeling__ReviewOut"];
export type Decision = S["DecisionOut"];
export type DecideIn = S["DecideIn"];
export type BulkIn = S["BulkIn"];
export type QueueState = NonNullable<S["BulkIn"]["state"]>;
export interface LFilters { subject_id?: string; language?: string; type_id?: string; topic_id?: string; state?: QueueState }
const A = api.client;
const u = api.unwrap;
const clean = (f: LFilters): LFilters => Object.fromEntries(Object.entries(f).filter(([, v]) => v)) as LFilters;

export const labeling = {
  /** Claims the next item for this labeler (10-minute lease). */
  next: (f: LFilters) => u(A.POST("/v1/labeling/queue/next", { params: { query: clean(f) } })),
  get: (id: string) => u(A.GET("/v1/labeling/queue/{question_id}", { params: { path: { question_id: id } } })),
  decide: (id: string, body: DecideIn) => u(A.POST("/v1/labeling/queue/{question_id}/decide", { params: { path: { question_id: id } }, body })),
  undo: (decisionId: string) => u(A.POST("/v1/labeling/decisions/{decision_id}/undo", { params: { path: { decision_id: decisionId } } })),
  stats: (days = 7) => u(A.GET("/v1/labeling/stats", { params: { query: { days } } })),
  bulkApprove: (body: BulkIn) => u(A.POST("/v1/admin/labeling/bulk-approve", { body })),
  sampleAudit: (body: S["AuditSampleIn"]) => u(A.POST("/v1/admin/labeling/audit/sample", { body })),
  agreement: (f: LFilters) => u(A.GET("/v1/admin/labeling/audit/agreement", { params: { query: clean(f) } })),
  solve: (question_ids: string[]) => u(A.POST("/v1/admin/labeling/solve", { body: { question_ids } })),
};
