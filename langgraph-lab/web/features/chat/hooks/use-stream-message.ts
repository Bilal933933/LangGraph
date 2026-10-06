"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createConversation } from "../lib/chat-api";
import { streamConversationMessage } from "../lib/chat-stream";
import { useChatStore } from "../store/chat-store";
import { conversationKey, conversationsKey } from "./use-conversations";

/** إرسال متدفق: send/sending/retryLast (المسار الوحيد للإرسال). */
export function useStreamMessage(pageConversationId: number | null) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [sending, setSending] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const current = abortRef.current;
    return () => current?.abort();
  }, []);

  function fail(message: string) {
    toast.error("تعذر إرسال الرسالة", {
      description: message,
      action: { label: "إعادة المحاولة", onClick: () => retryLast() },
    });
  }

  async function send(text: string) {
    await sendTo(text, pageConversationId);
  }

  async function sendTo(text: string, conversationId: number | null) {
    if (sending) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setSending(true);
    const store = useChatStore.getState();
    try {
      let targetId = conversationId;
      if (targetId === null) {
        const created = await createConversation();
        targetId = created.id;
        await queryClient.invalidateQueries({ queryKey: conversationsKey });
      }
      const finalId = targetId;
      store.setLastSent({ conversationId: finalId, text });
      store.setStreamingText("");
      store.setStreamStage(null);
      await streamConversationMessage(
        finalId,
        text,
        {
          onStage: (node) => useChatStore.getState().setStreamStage(node),
          onToken: (delta) =>
            useChatStore
              .getState()
              .setStreamingText(useChatStore.getState().streamingText + delta),
          onDone: async ({ clarification }) => {
            const current = useChatStore.getState();
            current.setLastSent(null);
            current.setStreamingText("");
            current.setStreamStage(null);
            current.setClarification(clarification);
            await queryClient.invalidateQueries({
              queryKey: conversationKey(finalId),
            });
            await queryClient.invalidateQueries({ queryKey: conversationsKey });
            if (conversationId === null) router.push(`/chat/${finalId}`);
          },
          onError: (error) => {
            const current = useChatStore.getState();
            current.setStreamingText("");
            current.setStreamStage(null);
            fail(error.message);
          },
        },
        controller.signal,
      );
    } catch (error) {
      useChatStore.getState().setStreamingText("");
      useChatStore.getState().setStreamStage(null);
      fail(error instanceof Error ? error.message : "حدث خطأ غير متوقع.");
    } finally {
      setSending(false);
    }
  }

  function retryLast() {
    const lastSent = useChatStore.getState().lastSent;
    if (!lastSent || sending) return;
    if (pageConversationId === null) {
      router.push(`/chat/${lastSent.conversationId}`);
    }
    void sendTo(lastSent.text, lastSent.conversationId);
  }

  return { send, sending, retryLast };
}
