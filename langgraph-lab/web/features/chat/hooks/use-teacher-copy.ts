"use client";

import { useQuery } from "@tanstack/react-query";
import { getTeacherCopy } from "../lib/chat-api";
import type { TeacherCopyKind } from "../types";

export const teacherCopyKey = (id: number | null, kind: TeacherCopyKind) =>
  ["teacher-copy", id, kind] as const;

/** نسخة المعلم: جلب عند فتح النافذة فقط (بلا توليد في السيرفر). */
export function useTeacherCopy(
  conversationId: number | null,
  kind: TeacherCopyKind,
  enabled: boolean,
) {
  return useQuery({
    queryKey: teacherCopyKey(conversationId, kind),
    queryFn: () => {
      if (conversationId === null) throw new Error("لا محادثة مختارة.");
      return getTeacherCopy(conversationId, kind);
    },
    enabled: enabled && conversationId !== null,
    retry: false,
    staleTime: 30_000,
  });
}

