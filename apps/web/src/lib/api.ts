import { createApiClient, type components, type paths } from "@dtmai/api-client";
import { apiUrl } from "./env";
import { readTokens, writeTokens } from "./session";

let onUnauthorized: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => (onUnauthorized = fn);

let locale = "uz-Latn";
/** Keeps `Accept-Language` in sync with the UI locale (called from Providers). */
export const setApiLocale = (l: string) => (locale = l);

export const api = createApiClient({
  baseUrl: typeof window === "undefined" ? "" : apiUrl(),
  getToken: () => readTokens()?.access_token,
  getRefreshToken: () => readTokens()?.refresh_token,
  setTokens: writeTokens,
  onUnauthorized: () => onUnauthorized(),
  locale: () => locale,
});

type S = components["schemas"];
type Ok<P extends keyof paths, M extends keyof paths[P] = "get"> = paths[P][M] extends {
  responses: { 200: { content: { "application/json": infer R } } };
}
  ? R
  : never;

export type Me = S["MeOut"];
export type Stats = Ok<"/v1/me/stats">;
export type Subject = S["SubjectOut"];
export type Path = S["LearnerPathOut"];
export type PathLesson = S["LearnerLessonOut"];
export type SessionOut = Ok<"/v1/learning/sessions/{session_id}">;
export type ItemOut = SessionOut["items"][number];
export type AnswerOut = S["AnswerOut"];
export type FinishOut = S["FinishOut"];
export type Attempt = S["AttemptOut"];
export type AttemptResult = S["ResultOut"];
export type Mock = S["MockOut"];
export type Plan = S["PlanOut"];
export type Quest = S["QuestOut"];
export type League = S["LeagueOut"];
export type LyceumRow = S["LyceumSummary"];
export type LyceumDetail = S["LyceumDetail"];
export type Language = S["LanguageOut"];
export type BillingMe = Ok<"/v1/billing/me">;
export type Names = { uz?: string | null; ru?: string | null; en?: string | null };
export type Media = S["app__interfaces__http__v1___media__MediaOut"];
export type Passage = S["PublicPassageOut"];
export type PredictionView = S["PredictionViewOut"];
export type HistoryItem = S["HistoryItemOut"];
