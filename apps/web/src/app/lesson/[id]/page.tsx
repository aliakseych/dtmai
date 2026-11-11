import { LessonRoute } from "./LessonRoute";

// Static export: one pre-rendered shell; the host rewrites /lesson/* to it and the id is read client-side.
export function generateStaticParams() {
  return [{ id: "_" }];
}

export default function LessonPage() {
  return <LessonRoute />;
}
