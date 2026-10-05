"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage } from "../types";
import { MarkdownMessage } from "./markdown-message";
import {
  SourcesFromText,
  SourcesList,
  splitSourcesBlock,
} from "./sources-list";

function formatTime(value: number): string {
  try {
    return new Date(value).toLocaleTimeString("ar", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function MessageBubble({
  message,
  onRetry,
}: {
  message: ChatMessage;
  onRetry: () => void;
}) {
  if (message.role === "assistant") {
    const { body, lines } = splitSourcesBlock(message.text);
    const structured = message.sources ?? [];
    return (
      <div className="flex w-full flex-col gap-1">
        <MarkdownMessage text={body} />
        {structured.length > 0 ? (
          <SourcesList sources={structured} />
        ) : (
          <SourcesFromText lines={lines} />
        )}
        <time className="text-[11px] text-muted-foreground">
          {formatTime(message.createdAt)}
        </time>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex w-full flex-col gap-1",
        message.role === "user" ? "items-start" : "items-stretch",
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-3xl px-4 py-2 text-[15px] leading-8 whitespace-pre-wrap",
          message.role === "user" && "bg-muted text-foreground",
          message.role === "error" && "bg-destructive/10 text-destructive",
        )}
      >
        {message.text}
      </div>
      <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
        <time>{formatTime(message.createdAt)}</time>
        {message.role === "error" && (
          <button
            type="button"
            onClick={onRetry}
            className="underline underline-offset-2 hover:text-foreground"
          >
            إعادة المحاولة
          </button>
        )}
      </div>
    </div>
  );
}
