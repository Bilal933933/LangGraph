"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useChatStore } from "../store/chat-store";
import type { Clarification } from "../types";

const FIELD_LABELS: Record<string, string> = {
  topic: "موضوع الدرس",
  grade_level: "المستوى الدراسي",
  minutes: "زمن الحصة",
};

const PROFILE_CTA_KEY = "clarification-profile-cta-seen";

function readCtaSeen(): boolean {
  try {
    return window.localStorage.getItem(PROFILE_CTA_KEY) === "1";
  } catch {
    return false;
  }
}

function ClarificationForm({
  clarification,
  onDone,
}: {
  clarification: Clarification;
  onDone: (text: string | null) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [ctaSeen, setCtaSeen] = useState(readCtaSeen);
  const showProfileCta = clarification.profile_empty && !ctaSeen;

  function submit() {
    const parts = clarification.missing
      .map((field) => values[field]?.trim())
      .filter((v): v is string => Boolean(v));
    if (parts.length === 0) return;
    if (showProfileCta) {
      try {
        window.localStorage.setItem(PROFILE_CTA_KEY, "1");
      } catch {
        /* تجاهل */
      }
      setCtaSeen(true);
    }
    onDone(parts.join("، "));
  }

  return (
    <>
      <div className="flex flex-col gap-4">
        {clarification.missing.map((field) => (
          <div key={field} className="flex flex-col gap-2">
            <span className="text-sm font-medium">{FIELD_LABELS[field] ?? field}</span>
            {(clarification.suggestions[field] ?? []).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {(clarification.suggestions[field] ?? []).map((option) => (
                  <Button
                    key={option}
                    type="button"
                    variant={values[field] === option ? "default" : "outline"}
                    size="sm"
                    onClick={() => setValues((prev) => ({ ...prev, [field]: option }))}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}
            <Input
              value={values[field] ?? ""}
              onChange={(event) => setValues((prev) => ({ ...prev, [field]: event.target.value }))}
              placeholder={`اكتب ${FIELD_LABELS[field] ?? field}`}
              aria-label={FIELD_LABELS[field] ?? field}
            />
          </div>
        ))}
        {showProfileCta && (
          <p className="text-xs text-muted-foreground">
            احفظ مادتك وصفوفك مرة واحدة وسأقترحها لك مباشرة.
          </p>
        )}
      </div>
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={() => onDone(null)}>
          لاحقاً
        </Button>
        <Button type="button" onClick={submit}>
          إرسال
        </Button>
      </DialogFooter>
    </>
  );
}

export function ClarificationDialog({ onSubmit }: { onSubmit: (text: string) => void }) {
  const clarification = useChatStore((state) => state.clarification);
  const setClarification = useChatStore((state) => state.setClarification);

  if (!clarification) return null;

  function handleDone(text: string | null) {
    setClarification(null);
    if (text) onSubmit(text);
  }

  return (
    <Dialog open onOpenChange={(open) => !open && handleDone(null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>لتحضير الدرس أحتاج</DialogTitle>
          <DialogDescription>اختر اقتراحاً أو اكتب إجابتك لكل حقل.</DialogDescription>
        </DialogHeader>
        <ClarificationForm
          key={clarification.missing.join("|")}
          clarification={clarification}
          onDone={handleDone}
        />
      </DialogContent>
    </Dialog>
  );
}
