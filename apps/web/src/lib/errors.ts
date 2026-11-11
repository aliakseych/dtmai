import { ApiError, NetworkError } from "@dtmai/api-client";
import type { MessageKey } from "@dtmai/i18n";

const AUTH: Record<string, MessageKey> = {
  email_taken: "auth.err.emailTaken",
  invalid_credentials: "auth.err.credentials",
  email_not_verified: "auth.err.notVerified",
  invalid_code: "auth.err.code",
  weak_password: "auth.err.weak",
  invalid_email: "auth.err.email",
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
