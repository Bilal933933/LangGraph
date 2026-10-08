"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import { TypingIndicator } from "./typing-indicator";
import type { ChatMessage } from "../types";

export function MessageList({
  messages,
  sending,
  stage,
  onRetry,
  onTeacherCopy,
}: {
  messages: ChatMessage[];
  sending: boolean;
  stage?: string | null;
  onRetry: () => void;
  onTeacherCopy?: () => void;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, sending]);

  return (
    <ScrollArea className="min-h-0 flex-1 px-4">
      <div
        aria-live="polite"
        className="mx-auto flex w-full max-w-3xl flex-col gap-6 py-6"
      >
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onRetry={onRetry}
            onTeacherCopy={message.role === "assistant" ? onTeacherCopy : undefined}
          />
        ))}
        {sending && <TypingIndicator stage={stage} />}
        <div ref={endRef} />
      </div>
    </ScrollArea>
  );
}
