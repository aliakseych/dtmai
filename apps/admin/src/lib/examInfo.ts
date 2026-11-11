"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Faq = S["FaqAdminOut"];
export type FaqIn = S["FaqIn"];
export type ExamEvent = S["ExamEventOut"];
export type EventIn = S["EventIn"];
export type ExamProfile = S["ExamProfileOut"];
export type ProfilePatch = S["ProfilePatch"];
export type ExamSection = S["ExamSectionOut"];
export type CertRule = S["CertRuleOut"];
export type CertRuleIn = S["CertRuleIn"];
export type CertRuleCreate = S["CertRuleCreate"];

const A = api.client;
const u = api.unwrap;

export const examInfo = {
  faq: {
    list: () => u(A.GET("/v1/admin/exam-info/faq")),
    create: (body: FaqIn) => u(A.POST("/v1/admin/exam-info/faq", { body })),
    update: (faq_id: string, body: FaqIn) => u(A.PUT("/v1/admin/exam-info/faq/{faq_id}", { params: { path: { faq_id } }, body })),
    remove: (faq_id: string) => u(A.DELETE("/v1/admin/exam-info/faq/{faq_id}", { params: { path: { faq_id } } })),
  },
  events: {
    list: () => u(A.GET("/v1/admin/exam-info/events")),
    create: (body: EventIn) => u(A.POST("/v1/admin/exam-info/events", { body })),
    update: (event_id: string, body: EventIn) => u(A.PUT("/v1/admin/exam-info/events/{event_id}", { params: { path: { event_id } }, body })),
    remove: (event_id: string) => u(A.DELETE("/v1/admin/exam-info/events/{event_id}", { params: { path: { event_id } } })),
  },
  profiles: {
    list: () => u(A.GET("/v1/admin/exam-info/profiles")),
    patch: (profile_id: string, body: ProfilePatch) => u(A.PATCH("/v1/admin/exam-info/profiles/{profile_id}", { params: { path: { profile_id } }, body })),
    setSubject: (section_id: string, subject_id: string | null) =>
      u(A.PATCH("/v1/admin/exam-info/sections/{section_id}", { params: { path: { section_id } }, body: { subject_id } })),
  },
  rules: {
    create: (body: CertRuleCreate) => u(A.POST("/v1/admin/exam-info/certificate-rules", { body })),
    update: (rule_id: string, body: CertRuleIn) => u(A.PUT("/v1/admin/exam-info/certificate-rules/{rule_id}", { params: { path: { rule_id } }, body })),
    remove: (rule_id: string) => u(A.DELETE("/v1/admin/exam-info/certificate-rules/{rule_id}", { params: { path: { rule_id } } })),
  },
};
