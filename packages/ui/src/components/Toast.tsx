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

export function ToastProvider({ children, duration = 4000 }: { children: ReactNode; duration?: number }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const push = useCallback(
    (text: string, tone: ToastTone = "info") => {
      const id = Date.now() + Math.random();
      setItems((xs) => [...xs, { id, text, tone }]);
      setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), duration);
    },
    [duration],
  );
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
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
