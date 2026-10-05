"use client";

import type { ChatSource } from "../types";

export function splitSourcesBlock(text: string): {
  body: string;
  lines: string[];
} {
  const marker = "\n---\nالمصادر:";
  const index = text.lastIndexOf(marker);
  if (index === -1) return { body: text, lines: [] };
  const lines = text
    .slice(index + marker.length)
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^\d+\.\s/.test(line));
  if (lines.length === 0) return { body: text, lines: [] };
  return { body: text.slice(0, index).trimEnd(), lines };
}

export function SourcesList({ sources }: { sources: ChatSource[] }) {
  if (sources.length === 0) return null;
  return (
    <details className="mt-2 w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-[13px] leading-7">
      <summary className="cursor-pointer font-medium text-foreground">
        المصادر ({sources.length})
      </summary>
      <ol className="mt-1 list-decimal space-y-1 pe-5 text-muted-foreground">
        {sources.map((source, index) => {
          const label = source.title || source.lesson || `مقطع ${index + 1}`;
          const meta = [source.subject, source.lesson]
            .filter((part) => part && part !== label)
            .join(" / ");
          return (
            <li key={`${label}-${index}`}>
              <span className="text-foreground">{label}</span>
              {meta && <span> ({meta})</span>}
            </li>
          );
        })}
      </ol>
    </details>
  );
}

export function SourcesFromText({ lines }: { lines: string[] }) {
  if (lines.length === 0) return null;
  return (
    <details className="mt-2 w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-[13px] leading-7">
      <summary className="cursor-pointer font-medium text-foreground">
        المصادر ({lines.length})
      </summary>
      <ol className="mt-1 list-decimal space-y-1 pe-5 text-muted-foreground">
        {lines.map((line) => (
          <li key={line}>{line.replace(/^\d+\.\s*/, "")}</li>
        ))}
      </ol>
    </details>
  );
}
