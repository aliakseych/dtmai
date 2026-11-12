"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type QuestTemplate = S["QuestTemplateOut"];
export type QuestTemplateIn = S["QuestTemplateIn"];
export type Tier = S["TierOut"];
export type GameConfig = S["ConfigModel"];
const A = api.client;
const u = api.unwrap;

export const gamification = {
  quests: () => u(A.GET("/v1/admin/gamification/quest-templates")),
  createQuest: (body: QuestTemplateIn) => u(A.POST("/v1/admin/gamification/quest-templates", { body })),
  updateQuest: (template_id: string, body: QuestTemplateIn) =>
    u(A.PUT("/v1/admin/gamification/quest-templates/{template_id}", { params: { path: { template_id } }, body })),
  tiers: () => u(A.GET("/v1/admin/gamification/league-tiers")),
  saveTiers: (tiers: Tier[]) => u(A.PUT("/v1/admin/gamification/league-tiers", { body: { tiers } })),
  rollover: () => u(A.POST("/v1/admin/gamification/league-rollover")),
  config: () => u(A.GET("/v1/admin/gamification/config")),
  saveConfig: (body: GameConfig) => u(A.PUT("/v1/admin/gamification/config", { body })),
};
