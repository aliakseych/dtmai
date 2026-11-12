import type { ButtonHTMLAttributes } from "react";
import { cn } from "../cn";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "super";

/**
 * Duolingo-style 3D buttons: a solid "edge" drawn as a bottom box-shadow
 * (--edge) that collapses on press while the face moves down, so the layout
 * box never changes size.
 */
const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-brand text-white [--edge:var(--color-brand-deep)] hover:brightness-110",
  secondary:
    "border-2 border-line bg-white text-brand [--edge:var(--color-line)] hover:bg-snow",
  danger: "bg-red text-white [--edge:var(--color-red-deep)] hover:brightness-105",
  ghost: "bg-transparent text-brand shadow-none hover:bg-brand-soft",
  super: "bg-accent text-black [--edge:var(--color-accent-deep)] hover:brightness-105",
};

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  block?: boolean;
};

const BASE =
  "inline-flex select-none items-center justify-center gap-2 rounded-2xl px-5 py-3 text-[15px] font-extrabold uppercase tracking-wide transition-[transform,box-shadow,filter,background-color] duration-100";
const RAISED =
  "shadow-[0_4px_0_0_var(--edge)] active:translate-y-[4px] active:shadow-[0_0_0_0_var(--edge)] disabled:cursor-not-allowed disabled:border-transparent disabled:bg-line disabled:text-ink-mute disabled:shadow-[0_4px_0_0_var(--color-line-deep)] disabled:hover:brightness-100 disabled:active:translate-y-0 disabled:active:shadow-[0_4px_0_0_var(--color-line-deep)]";
const FLAT = "disabled:cursor-not-allowed disabled:text-ink-mute disabled:hover:bg-transparent";

export function buttonClass(variant: ButtonVariant = "primary", block?: boolean, extra?: string): string {
  return cn(BASE, variant === "ghost" ? FLAT : RAISED, VARIANTS[variant], block && "w-full", extra);
}

export function Button({ variant = "primary", block, className, type = "button", ...rest }: ButtonProps) {
  return <button type={type} className={buttonClass(variant, block, className)} {...rest} />;
}
