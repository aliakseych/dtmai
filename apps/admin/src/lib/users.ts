"use client";
import { api } from "./api";

/** PENDING CONTRACT: `GET /v1/admin/users?q=&limit=&offset=` is not in openapi.json yet; this shape is what the admin UI expects. */
export interface AdminUser { id: string; email: string | null; display_name: string | null; roles: string[]; created_at: string; telegram_id?: number | null; is_active?: boolean }
export const users = {
  search: (q: string) => api.raw<{ total: number; items: AdminUser[] }>("GET", "/v1/admin/users", { query: { q, limit: 50 } }),
  setRoles: (id: string, roles: string[]) => api.raw<AdminUser>("PUT", `/v1/admin/users/${id}/roles`, { body: { roles } }),
};
