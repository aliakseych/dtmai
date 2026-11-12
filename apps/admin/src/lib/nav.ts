/** `label`/`title` are i18n keys; `keywords` are extra English search hints for the command palette. */
export interface NavItem { href: string; label: string; keywords?: string }
export interface NavSection { title: string; items: NavItem[] }

export const NAV: NavSection[] = [
  { title: "admin.nav.content", items: [
    { href: "/questions/", label: "admin.nav.questions", keywords: "questions editor import" },
    { href: "/labeling/", label: "admin.nav.labeling", keywords: "review queue audit" },
    { href: "/coverage/", label: "admin.nav.coverage", keywords: "pool verified min" },
    { href: "/generation/", label: "admin.nav.generation", keywords: "ai generate" },
    { href: "/ingestion/", label: "admin.nav.ingestion", keywords: "files pdf import batch" },
  ] },
  { title: "admin.nav.catalog", items: [
    { href: "/subjects/", label: "admin.nav.subjects" },
    { href: "/topics/", label: "admin.nav.topics" },
    { href: "/question-types/", label: "admin.nav.questionTypes" },
    { href: "/paths/", label: "admin.nav.paths", keywords: "units lessons" },
    { href: "/blueprints/", label: "admin.nav.blueprints", keywords: "mock exam" },
    { href: "/sources/", label: "admin.nav.sources", keywords: "sources previous year" },
  ] },
  { title: "admin.nav.platform", items: [
    { href: "/ai/", label: "admin.nav.ai", keywords: "openrouter routes limits" },
    { href: "/lyceums/", label: "admin.nav.lyceums", keywords: "profiles reps moderation posts import edu.uz quota" },
    { href: "/fields/", label: "admin.nav.fields", keywords: "speciality edu.uz subjects mapping onboarding" },
    { href: "/exam-info/", label: "admin.nav.examInfo", keywords: "faq dates certificates exam profile directions ielts" },
    { href: "/billing/", label: "admin.nav.billing", keywords: "premium subscription" },
    { href: "/users/", label: "admin.nav.users", keywords: "learners accounts roles stats" },
    { href: "/admins/", label: "admin.nav.admins", keywords: "create staff editor admin accounts" },
    { href: "/labelers/", label: "admin.nav.labelers", keywords: "system labeler activity leaderboard credentials" },
    { href: "/notifications/", label: "admin.nav.notifications" },
    { href: "/gamification/", label: "admin.nav.gamification", keywords: "hearts xp gems" },
    { href: "/audit/", label: "admin.nav.audit" },
  ] },
];
