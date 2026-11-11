"use client";
import { api } from "./api";

/** PENDING CONTRACT: `POST /v1/admin/notifications/broadcast` is not in openapi.json yet; this shape is what the admin UI sends. */
export interface BroadcastIn { channel: "telegram" | "email" | "push"; locale?: string | null; title: string; body: string; dry_run: boolean }
export const notifications = {
  broadcast: (body: BroadcastIn) => api.raw<{ recipients: number; queued: boolean }>("POST", "/v1/admin/notifications/broadcast", { body }),
};
