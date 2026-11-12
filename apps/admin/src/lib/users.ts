"use client";
import type { components, operations } from "@dtmai/api-client";
import { ApiError } from "@dtmai/api-client";
import { useToast } from "@dtmai/ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import { useT } from "./i18n";
import { errMsg } from "./util";

type S = components["schemas"];
export type AdminUser = S["AdminUserOut"];
export type UserPatch = S["AdminUserPatch"];
export type StaffCreate = S["AdminUserCreate"];
export type UserStats = S["app__interfaces__http__v1__learning__StatsOut"];
export type UserListQuery = NonNullable<operations["identity_admin_list_users"]["parameters"]["query"]>;
export type UserSort = NonNullable<UserListQuery["sort"]>;
export type UserStatus = AdminUser["status"];

export const ALL_ROLES = ["student", "editor", "admin", "labeler", "lyceum_rep"] as const;
export const STAFF_ROLES = ["admin", "editor", "labeler", "lyceum_rep"] as const;

const A = api.client;
const u = api.unwrap;
const clean = <T extends object>(q: T): T => Object.fromEntries(Object.entries(q).filter(([, v]) => v !== "" && v != null)) as T;

export const users = {
  list: (query: UserListQuery) => u(A.GET("/v1/admin/users", { params: { query: clean(query) } })),
  get: (id: string) => u(A.GET("/v1/admin/users/{user_id}", { params: { path: { user_id: id } } })),
  create: (body: StaffCreate) => u(A.POST("/v1/admin/users", { body })),
  patch: (id: string, body: UserPatch) => u(A.PATCH("/v1/admin/users/{user_id}", { params: { path: { user_id: id } }, body })),
  resetPassword: (id: string, password: string) => u(A.POST("/v1/admin/users/{user_id}/reset-password", { params: { path: { user_id: id } }, body: { password } })),
  stats: (id: string) => u(A.GET("/v1/admin/users/{user_id}/stats", { params: { path: { user_id: id } } })),
};

/** Messages for the stable protection error codes; falls back to the server text. */
const CODE_MSG: Record<string, string> = {
  account_disabled: "admin.usersErr.account_disabled",
  last_admin: "admin.usersErr.last_admin",
  self_disable: "admin.usersErr.self_disable",
  self_demotion: "admin.usersErr.self_demotion",
  invalid_role: "admin.usersErr.invalid_role",
  email_taken: "admin.usersErr.email_taken",
};
export const userErrMsg = (e: unknown, t: (k: string) => string) => (e instanceof ApiError && CODE_MSG[e.code] ? t(CODE_MSG[e.code]!) : errMsg(e));

/** Mutation that invalidates the given query keys and surfaces (protection) errors as toasts. */
export function useUserAct<A, R>(fn: (a: A) => Promise<R>, invalidate: readonly (readonly unknown[])[], ok?: string) {
  const qc = useQueryClient();
  const toast = useToast();
  const t = useT();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      for (const k of invalidate) void qc.invalidateQueries({ queryKey: k as unknown[] });
      if (ok) toast(t(ok), "success");
    },
    onError: (e) => toast(userErrMsg(e, t), "error"),
  });
}
