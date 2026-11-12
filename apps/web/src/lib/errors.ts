import { ApiError, NetworkError } from "@dtmai/api-client";
import type { MessageKey } from "@dtmai/i18n";

const AUTH: Record<string, MessageKey> = {
  email_taken: "auth.err.emailTaken",
  invalid_credentials: "auth.err.credentials",
  email_not_verified: "auth.err.notVerified",
  invalid_code: "auth.err.code",
  weak_password: "auth.err.weak",
  invalid_email: "auth.err.email",
  validation_failed: "auth.err.required",
  telegram_invalid: "auth.err.telegram",
  telegram_expired: "auth.err.telegram",
};

/** Maps an API/network failure to a localized message key. */
export function authErrorKey(e: unknown): MessageKey {
  if (e instanceof NetworkError) return "common.offline";
  if (e instanceof ApiError) return AUTH[e.code] ?? "common.error";
  return "common.error";
}

export const isCode = (e: unknown, code: string) => e instanceof ApiError && e.code === code;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export type FieldErrors = Partial<Record<"name" | "email" | "password" | "code", MessageKey>>;

/** Client-side checks shared by the auth forms; returns a localized message key or null. */
export const checkRequired = (v: string): MessageKey | null => (v.trim() ? null : "auth.err.required");
export const checkEmail = (v: string): MessageKey | null =>
  !v.trim() ? "auth.err.required" : EMAIL_RE.test(v.trim()) ? null : "auth.err.email";
export const checkPassword = (v: string): MessageKey | null =>
  !v ? "auth.err.required" : v.length < 8 ? "auth.err.weak" : null;

const FIELD_KEY: Record<string, MessageKey> = { email: "auth.err.email", password: "auth.err.weak", name: "auth.err.required", code: "auth.err.code" };

/** Maps a 422 problem (`errors[].loc`) onto form fields; empty when the failure is not field-level. */
export function serverFieldErrors(e: unknown): FieldErrors {
  const out: FieldErrors = {};
  if (!(e instanceof ApiError) || e.status !== 422) return out;
  const list = (e.problem as { errors?: { loc?: unknown[] }[] } | undefined)?.errors ?? [];
  for (const it of list) {
    const field = String(it.loc?.[it.loc.length - 1] ?? "");
    if (field in FIELD_KEY) out[field as keyof FieldErrors] ??= FIELD_KEY[field];
  }
  return out;
}
