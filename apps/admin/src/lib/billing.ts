"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Plan = S["PlanOut"];
export type PlanCreate = S["PlanCreate"];
export type PlanPatch = S["PlanPatch"];
export type Subscription = S["SubscriptionOut"];
const A = api.client;
const u = api.unwrap;

export const billing = {
  plans: () => u(A.GET("/v1/admin/billing/plans")),
  createPlan: (body: PlanCreate) => u(A.POST("/v1/admin/billing/plans", { body })),
  updatePlan: (code: string, body: PlanPatch) => u(A.PATCH("/v1/admin/billing/plans/{code}", { params: { path: { code } }, body })),
  removePlan: (code: string) => u(A.DELETE("/v1/admin/billing/plans/{code}", { params: { path: { code } } })),
  grant: (body: S["GrantIn"]) => u(A.POST("/v1/admin/billing/grants", { body })),
  subscriptions: (user_id: string) => u(A.GET("/v1/admin/billing/users/{user_id}/subscriptions", { params: { path: { user_id } } })),
  revoke: (subscription_id: string) => u(A.POST("/v1/admin/billing/subscriptions/{subscription_id}/revoke", { params: { path: { subscription_id } } })),
};
