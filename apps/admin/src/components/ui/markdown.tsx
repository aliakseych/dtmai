"use client";
import katex from "katex";
import { useMemo } from "react";
import { mediaUrl } from "@/lib/env";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function tex(src: string, display: boolean): string {
  try {
    return katex.renderToString(src, { displayMode: display, throwOnError: true, output: "htmlAndMathml" });
  } catch (e) {
    return `<span class="rounded bg-red-soft px-1 text-red-deep" title="${esc((e as Error).message)}">${esc(src)}</span>`;
  }
}

function inline(s: string): string {
  return esc(s)
    .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (_, a, u) => `<img alt="${a}" src="${esc(u.startsWith("http") ? u : mediaUrl(u))}" class="my-1 max-h-64 rounded" />`)
    .replace(/`([^`]+)`/g, "<code class='rounded bg-snow px-1'>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\n/g, "<br/>");
}

/** Minimal markdown + KaTeX: `$$..$$` display, `$..$` inline, **bold**, *em*, `code`, images. HTML is escaped. */
export function renderMd(src: string): string {
  const out: string[] = [];
  const re = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;
  let last = 0;
  for (let m = re.exec(src); m; m = re.exec(src)) {
    out.push(inline(src.slice(last, m.index)));
    out.push(m[1] !== undefined ? `<div class="my-1 overflow-x-auto">${tex(m[1], true)}</div>` : tex(m[2]!, false));
    last = m.index + m[0].length;
  }
  out.push(inline(src.slice(last)));
  return out.join("");
}

export function Md({ text, className }: { text: string; className?: string }) {
  const html = useMemo(() => renderMd(text), [text]);
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
