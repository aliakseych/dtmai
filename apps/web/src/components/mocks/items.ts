import type { Attempt, ItemOut } from "@/lib/api";

type AttemptItem = Attempt["items"][number];

/** Attempt items differ from session items only by a nullable topic; QuestionBody never reads it. */
export const toItem = (i: AttemptItem): ItemOut => ({
  ...i,
  topic_id: i.topic_id ?? "",
  children: i.children?.map((c) => toItem(c as AttemptItem)),
});
export const toItems = (items: Attempt["items"]): ItemOut[] => items.map(toItem);
