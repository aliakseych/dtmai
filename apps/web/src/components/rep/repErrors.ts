import { ApiError, NetworkError } from "@dtmai/api-client";
import type { MessageKey } from "@dtmai/i18n";

const REP: Record<string, MessageKey> = {
  guest_cannot_apply: "rep.err.guest_cannot_apply",
  rep_forbidden: "rep.err.rep_forbidden",
  rep_application_pending: "rep.err.rep_application_pending",
  rep_already_approved: "rep.err.rep_already_approved",
  post_state: "rep.err.post_state",
  reason_required: "rep.err.reason_required",
  starts_at_required: "rep.err.starts_at_required",
  link_required: "rep.err.link_required",
  invalid_link: "rep.err.invalid_link",
};

/** Maps a rep-portal API failure to a localized message key. */
export function repErrorKey(e: unknown): MessageKey {
  if (e instanceof NetworkError) return "common.offline";
  if (e instanceof ApiError) return REP[e.code] ?? "common.error";
  return "common.error";
}
