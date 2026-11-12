"use client";
import { Fragment, type ReactNode } from "react";
import { RichText } from "@/components/RichText";

const INLINE = /(`[^`\n]+`|\*\*[^*\n]+?\*\*|__[^_\n]+?__|\*[^*\s][^*\n]*?\*|(?<![\w])_[^_\s][^_\n]*?_(?![\w]))/g;

function inline(src: string): ReactNode[] {
  return src.split(INLINE).map((p, i) => {
    if (!p) return null;
    if (p.length > 2 && p.startsWith("`") && p.endsWith("`"))
      return <code key={i} className="rounded bg-snow px-1 font-mono text-[0.9em]">{p.slice(1, -1)}</code>;
    if (p.length > 4 && (p.startsWith("**") || p.startsWith("__")) && p.slice(-2) === p.slice(0, 2))
      return <strong key={i}>{inline(p.slice(2, -2))}</strong>;
    if (p.length > 2 && (p[0] === "*" || p[0] === "_") && p.endsWith(p[0]))
      return <em key={i}>{inline(p.slice(1, -1))}</em>;
    return <RichText key={i} text={p} className="whitespace-pre-line" />;
  });
}

type Block =
  | { k: "h"; level: number; text: string }
  | { k: "hr" }
  | { k: "code"; text: string }
  | { k: "ul" | "ol"; items: string[] }
  | { k: "p"; text: string };

function parse(src: string): Block[] {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out: Block[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) out.push({ k: "p", text: para.join("\n") });
    para = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/^\s*```/.test(line)) {
      flush();
      const code: string[] = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) code.push(lines[i++]);
      out.push({ k: "code", text: code.join("\n") });
      continue;
    }
    const h = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/.exec(line);
    if (h) {
      flush();
      out.push({ k: "h", level: h[1].length, text: h[2] });
      continue;
    }
    if (/^\s{0,3}([-*_])(\s*\1){2,}\s*$/.test(line)) {
      flush();
      out.push({ k: "hr" });
      continue;
    }
    const li = /^\s*([-*+]|\d+[.)])\s+(.*)$/.exec(line);
    if (li) {
      flush();
      const kind = /\d/.test(li[1]) ? "ol" : "ul";
      const last = out[out.length - 1];
      if (last && last.k === kind) last.items.push(li[2]);
      else out.push({ k: kind, items: [li[2]] });
      continue;
    }
    if (!line.trim()) {
      flush();
      continue;
    }
    para.push(line.trim());
  }
  flush();
  return out;
}

const HEADING = ["text-xl", "text-lg", "text-base", "text-base", "text-sm", "text-sm"];

/** Safe Markdown subset: headings, bold/italic, lists, hr, code. No raw HTML is ever injected. */
export function Markdown({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-2 break-words">
      {parse(text).map((b, i) => {
        switch (b.k) {
          case "h":
            return <p key={i} className={`font-extrabold ${HEADING[b.level - 1]}`}>{inline(b.text)}</p>;
          case "hr":
            return <hr key={i} className="border-line" />;
          case "code":
            return <pre key={i} className="overflow-x-auto rounded-xl bg-snow p-3 font-mono text-sm">{b.text}</pre>;
          case "ul":
          case "ol": {
            const L = b.k;
            return (
              <L key={i} className={`${L === "ul" ? "list-disc" : "list-decimal"} flex flex-col gap-1 pl-6`}>
                {b.items.map((it, j) => <li key={j}>{inline(it)}</li>)}
              </L>
            );
          }
          default:
            return <p key={i}><Fragment>{inline(b.text)}</Fragment></p>;
        }
      })}
    </div>
  );
}
