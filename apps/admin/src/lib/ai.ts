"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Route = S["RouteIO"];
export type Limits = S["LimitsIO"];
export type Spend = S["SpendReportOut"];
export type AiTask = S["Task"];
export const AI_TASKS: AiTask[] = ["extract", "solve", "judge", "explain", "tutor", "generate"];
const A = api.client;
const u = api.unwrap;

export const ai = {
  routes: () => u(A.GET("/v1/admin/ai/routes")),
  saveRoute: (body: Route) => u(A.PUT("/v1/admin/ai/routes", { body })),
  removeRoute: (task: AiTask, slot: number) => u(A.DELETE("/v1/admin/ai/routes/{task}/{slot}", { params: { path: { task, slot } } })),
  limits: () => u(A.GET("/v1/admin/ai/limits")),
  saveLimits: (body: Limits) => u(A.PUT("/v1/admin/ai/limits", { body })),
  spend: (days: number) => u(A.GET("/v1/admin/ai/spend", { params: { query: { days } } })),
};
