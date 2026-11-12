import type { components } from "@dtmai/api-client";

type S = components["schemas"];
export type DailyStat = S["DailyStatOut"];
export type SubjectStat = S["SubjectStatOut"];
export type MockStat = S["MockStatOut"];
export type LearnerStats = S["app__interfaces__http__v1__learning__StatsOut"];
