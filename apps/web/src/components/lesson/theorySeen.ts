const key = (lessonId: string) => `dtmai.theory.${lessonId}`;

/** Whether the learner already went through a lesson's theory cards (per device). */
export function isTheorySeen(lessonId: string): boolean {
  try {
    return window.localStorage.getItem(key(lessonId)) === "1";
  } catch {
    return false;
  }
}

export function markTheorySeen(lessonId: string): void {
  try {
    window.localStorage.setItem(key(lessonId), "1");
  } catch {
    /* storage unavailable: the cards just show again next time */
  }
}
