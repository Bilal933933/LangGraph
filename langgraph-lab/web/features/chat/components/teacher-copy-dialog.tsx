"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useTeacherCopy } from "../hooks/use-teacher-copy";
import type { TeacherCopyKind } from "../types";
import { MarkdownMessage } from "./markdown-message";

const KINDS: { value: TeacherCopyKind; label: string }[] = [
  { value: "quiz", label: "اختبار" },
  { value: "worksheet", label: "ورقة عمل" },
];

export function TeacherCopyDialog({
  conversationId,
  open,
  onOpenChange,
}: {
  conversationId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [kind, setKind] = useState<TeacherCopyKind>("quiz");
  const copy = useTeacherCopy(conversationId, kind, open);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85dvh] max-w-2xl">
        <DialogHeader>
          <DialogTitle>نسخة المعلم</DialogTitle>
          <DialogDescription>
            تتضمن الإجابات — لا تشاركها مع الطلاب.
          </DialogDescription>
        </DialogHeader>
        <div className="flex gap-2">
          {KINDS.map((item) => (
            <Button
              key={item.value}
              type="button"
              variant={kind === item.value ? "default" : "outline"}
              size="sm"
              onClick={() => setKind(item.value)}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <ScrollArea
          className={cn("min-h-0 max-h-[55dvh] rounded-lg border border-border p-4")}
        >
          {copy.isPending ? (
            <p className="text-sm text-muted-foreground">جارٍ التحميل…</p>
          ) : copy.isError ? (
            <p className="text-sm text-muted-foreground">
              لا توجد نسخة معلم بعد — ولّد اختبارًا أو ورقة عمل أولًا.
            </p>
          ) : (
            <MarkdownMessage text={copy.data.text} />
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

