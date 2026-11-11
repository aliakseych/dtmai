export interface NavItem { href: string; label: string; keywords?: string }
export interface NavSection { title: string; items: NavItem[] }

export const NAV: NavSection[] = [
  { title: "Content", items: [
    { href: "/questions/", label: "Question bank", keywords: "questions editor import" },
    { href: "/labeling/", label: "Labeling cockpit", keywords: "review queue audit" },
    { href: "/coverage/", label: "Coverage", keywords: "pool verified min" },
    { href: "/generation/", label: "Generation runs", keywords: "ai generate" },
    { href: "/ingestion/", label: "Ingestion", keywords: "files pdf import batch" },
  ] },
  { title: "Catalog", items: [
    { href: "/subjects/", label: "Subjects" },
    { href: "/topics/", label: "Topics" },
    { href: "/question-types/", label: "Question types" },
    { href: "/paths/", label: "Paths & lessons", keywords: "units lessons" },
    { href: "/blueprints/", label: "Mock blueprints", keywords: "mock exam" },
    { href: "/sources/", label: "Question bases", keywords: "sources previous year" },
  ] },
  { title: "Platform", items: [
    { href: "/ai/", label: "AI models & spend", keywords: "openrouter routes limits" },
    { href: "/lyceums/", label: "Lyceums", keywords: "profiles reps moderation posts import edu.uz quota" },
    { href: "/fields/", label: "Fields of study", keywords: "speciality edu.uz subjects mapping onboarding" },
    { href: "/exam-info/", label: "Exam info", keywords: "faq dates certificates exam profile directions ielts" },
    { href: "/billing/", label: "Plans & grants", keywords: "premium subscription" },
    { href: "/users/", label: "Users", keywords: "learners accounts roles stats" },
    { href: "/admins/", label: "Admins & staff", keywords: "create staff editor admin accounts" },
    { href: "/labelers/", label: "Labelers", keywords: "system labeler activity leaderboard credentials" },
    { href: "/notifications/", label: "Notifications" },
    { href: "/gamification/", label: "Quests & leagues", keywords: "hearts xp gems" },
    { href: "/audit/", label: "Audit log" },
  ] },
];
