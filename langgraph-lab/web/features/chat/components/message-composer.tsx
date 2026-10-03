"use client";

import { useEffect, useRef } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function MessageComposer({
  draft,
  onDraftChange,
  onSubmit,
  sending,
  maxLength,
}: {
  draft: string;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
  sending: boolean;
  maxLength: number;
}) {
  const areaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const element = areaRef.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [draft]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    onSubmit();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-5">
      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-2 rounded-[28px] border border-border bg-muted/60 p-2 ps-4 focus-within:border-ring"
      >
        <textarea
          ref={areaRef}
          rows={1}
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="اسأل أي شيء"
          maxLength={maxLength}
          disabled={sending}
          aria-label="نص الرسالة"
          className="max-h-[200px] flex-1 resize-none bg-transparent text-[15px] leading-7 outline-none placeholder:text-muted-foreground disabled:opacity-60"
        />
        <Button
          type="submit"
          size="icon"
          disabled={sending || draft.trim().length === 0}
          aria-label="إرسال"
          className="size-9 shrink-0 rounded-full"
        >
          {sending ? <Loader2 className="animate-spin" /> : <ArrowUp />}
        </Button>
      </form>
      <p className="mt-1 text-center text-[11px] text-muted-foreground">
        Enter للإرسال • Shift+Enter لسطر جديد • {draft.length}/{maxLength}
      </p>
    </div>
  );
}
