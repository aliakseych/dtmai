"use client";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { cn } from "../cn";

type ToastTone = "info" | "success" | "error";
type ToastItem = { id: number; text: string; tone: ToastTone };
const ToastContext = createContext<(text: string, tone?: ToastTone) => void>(() => {});

const TONES: Record<ToastTone, string> = {
  info: "bg-brand text-white border-brand",
  success: "bg-brand text-white border-brand-deep",
  error: "bg-red-deep text-white border-red-ink",
};

export function ToastProvider({ children, duration = 4000, position = "top" }: { children: ReactNode; duration?: number; position?: "top" | "bottom" }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const push = useCallback(
    (text: string, tone: ToastTone = "info") => {
      const id = Date.now() + Math.random();
      // A success supersedes stale error toasts so an old failure never sits beside "Saved".
      setItems((xs) => [...(tone === "success" ? xs.filter((x) => x.tone !== "error") : xs), { id, text, tone }]);
      setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), duration);
    },
    [duration],
  );
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className={cn("pointer-events-none fixed inset-x-0 z-50 flex items-center gap-2 px-4", position === "top" ? "top-4 flex-col" : "bottom-4 flex-col-reverse")}>
        {items.map((i) => (
          <div key={i.id} role={i.tone === "error" ? "alert" : "status"} className={cn("pointer-events-auto rounded-2xl border-b-4 px-5 py-3 font-extrabold", TONES[i.tone])}>
            {i.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
