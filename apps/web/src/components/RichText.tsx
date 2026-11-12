"use client";
import katex from "katex";
import "katex/dist/katex.min.css";
import { useMemo } from "react";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function math(src: string, display: boolean): string {
  try {
    return katex.renderToString(src, { displayMode: display, throwOnError: true });
  } catch {
    return `<span class="font-mono">${esc(src)}</span>`;
  }
}

/** Renders text with `$inline$` and `$$display$$` KaTeX; everything else is HTML-escaped. */
export function renderRich(src: string): string {
  return src
    .split(/(\$\$[\s\S]+?\$\$|\$(?=[^\s$])[^$\n]*?[^\s$]\$(?!\d)|\$[^\s$\d]\$(?!\d))/g)
    .map((p) => (p.startsWith("$$") && p.length > 4 ? math(p.slice(2, -2), true) : p.startsWith("$") && p.length > 2 && p.endsWith("$") ? math(p.slice(1, -1), false) : esc(p)))
    .join("");
}

export function RichText({ text, className }: { text: string; className?: string }) {
  const html = useMemo(() => renderRich(text), [text]);
  return <span className={className ?? "whitespace-pre-line leading-relaxed"} dangerouslySetInnerHTML={{ __html: html }} />;
}
