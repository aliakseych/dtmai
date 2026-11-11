import type { ButtonHTMLAttributes } from "react";
import { cn } from "../cn";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "super";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-green-deep text-white border-[#3d7300]",
  secondary: "bg-white text-blue border-line border-2 border-b-4 hover:bg-snow",
  danger: "bg-red-deep text-white border-[#8f1f1f]",
  ghost: "bg-transparent text-blue border-transparent hover:bg-blue-soft",
  super: "bg-gold text-ink border-gold-deep",
};

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  block?: boolean;
};

const BASE =
  "inline-flex select-none items-center justify-center gap-2 rounded-2xl px-5 py-3 text-[15px] font-extrabold uppercase tracking-wide transition active:translate-y-[2px] active:border-b-2 disabled:cursor-not-allowed disabled:bg-line disabled:text-[#afafaf] disabled:border-[#cfcfcf] disabled:active:translate-y-0 disabled:active:border-b-4";

export function buttonClass(variant: ButtonVariant = "primary", block?: boolean, extra?: string): string {
  const border = variant === "secondary" ? "" : variant === "ghost" ? "border-b-0 active:translate-y-0" : "border-b-4";
  return cn(BASE, border, VARIANTS[variant], block && "w-full", extra);
}

export function Button({ variant = "primary", block, className, type = "button", ...rest }: ButtonProps) {
  return <button type={type} className={buttonClass(variant, block, className)} {...rest} />;
}
