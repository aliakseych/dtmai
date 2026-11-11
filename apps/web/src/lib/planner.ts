import { ApiError, type components } from "@dtmai/api-client";
import type { Locale } from "@dtmai/i18n";
import { questHref } from "@/components/quests/QuestItem";
import { api, type Names, type Quest } from "./api";
import { pick } from "./localized";

/** Study planner + exam-info; every type comes from the generated OpenAPI schema. */
type S = components["schemas"];

export type TaskKind = S["TaskKind"];
export type TaskStatus = S["TaskStatus"];
export type TaskOut = S["TaskOut"];
export type DayOut = S["DayOut"];
export type RangeOut = S["RangeOut"];
export type TodayOut = S["TodayOut"];
export type HomeOut = S["HomeOut"];
export type SettingsIn = S["SettingsIn"];
export type SettingsOut = S["SettingsOut"];
export type Certificate = S["CertificateIO"];
export type AnalyticsOut = S["AnalyticsOut"];
export type DailyQuestionsOut = S["DailyQuestionsOut"];
export type DailyQuestionOut = S["DailyQuestionOut"];
export type DailyAnswerOut = S["DailyAnswerOut"];
export type ExamProfile = S["ExamProfileOut"];
export type ExamSection = S["ExamSectionOut"];
export type CertRule = S["CertRuleOut"];
export type ExamEvent = S["ExamEventOut"];
export type Faq = S["FaqOut"];

async function orNull<T>(p: Promise<T>): Promise<T | null> {
  try {
    return await p;
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export const listProfiles = () => api.unwrap(api.client.GET("/v1/exam-info/profiles"));
export const getProfile = (direction_code: string) => api.unwrap(api.client.GET("/v1/exam-info/profiles/{direction_code}", { params: { path: { direction_code } } }));
export const listEvents = (exam_year?: number) => api.unwrap(api.client.GET("/v1/exam-info/events", { params: { query: { exam_year } } }));
export const listFaq = (locale: Locale, category?: string) => api.unwrap(api.client.GET("/v1/exam-info/faq", { params: { query: { locale, category } } }));

/** `null` while the learner has not completed the wizard (404 plan_not_found). */
export const getSettings = () => orNull(api.unwrap(api.client.GET("/v1/study-plan/settings")));
/** Saving rebuilds the schedule from today. */
export const saveSettings = (body: SettingsIn) => api.unwrap(api.client.POST("/v1/study-plan/settings", { body }));
export const generatePlan = () => api.unwrap(api.client.POST("/v1/study-plan/generate"));
export const getHome = () => api.unwrap(api.client.GET("/v1/study-plan/home"));
export const getToday = () => orNull(api.unwrap(api.client.GET("/v1/study-plan/today")));
export const getWeek = (start?: string) => api.unwrap(api.client.GET("/v1/study-plan/week", { params: { query: { start } } }));
export const getMonth = (year: number, month: number) => api.unwrap(api.client.GET("/v1/study-plan/month", { params: { query: { year, month } } }));
export const completeTask = (task_id: string) => api.unwrap(api.client.POST("/v1/study-plan/tasks/{task_id}/complete", { params: { path: { task_id } } }));
export const getAnalytics = () => api.unwrap(api.client.GET("/v1/study-plan/analytics"));
export const getDailyQuestions = () => api.unwrap(api.client.GET("/v1/study-plan/daily-questions"));
export const answerDailyQuestion = (question_id: string, response: S["DailyAnswerIn"]["response"]) =>
  api.unwrap(api.client.POST("/v1/study-plan/daily-questions/{question_id}/answer", { params: { path: { question_id } }, body: { response } }));

/** Route that executes a task; mirrors `questHref`. */
export function taskHref(kind: TaskKind): string {
  return kind === "rush" ? "/practice/rush/" : questHref(kind);
}

/** Localized profile name with the same fallback chain as catalog names. */
export const profileName = (p: Pick<ExamProfile, "names" | "code">, l: Locale) => pick(p.names as Names, l) || p.code;
