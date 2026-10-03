"use client";

import { useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { postChat } from "../lib/chat-api";
import {
  createMessageId,
  ensureActiveChatId,
  useChatStore,
} from "../store/chat-store";

export function useSendMessage() {
  const targetRef = useRef<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (text: string) => {
      const chatId = ensureActiveChatId();
      targetRef.current = chatId;
      useChatStore.getState().pushMessage(chatId, {
        id: createMessageId(),
        role: "user",
        text,
        createdAt: Date.now(),
      });
      useChatStore.getState().setLastSent({ chatId, text });
      const reply = await postChat(text);
      return { chatId, reply };
    },
    onSuccess: ({ chatId, reply }) => {
      useChatStore.getState().pushMessage(chatId, {
        id: createMessageId(),
        role: "assistant",
        text: reply,
        createdAt: Date.now(),
      });
      useChatStore.getState().setLastSent(null);
    },
    onError: (error) => {
      const chatId = targetRef.current;
      const message =
        error instanceof Error ? error.message : "حدث خطأ غير متوقع.";
      if (chatId) {
        useChatStore.getState().pushMessage(chatId, {
          id: createMessageId(),
          role: "error",
          text: message,
          createdAt: Date.now(),
        });
      }
      toast.error("تعذر إرسال الرسالة", {
        description: "تأكد أن السيرفر يعمل وأن GOOGLE_API_KEY مضبوط.",
      });
    },
  });

  function retryLast() {
    const lastSent = useChatStore.getState().lastSent;
    if (!lastSent || mutation.isPending) return;
    targetRef.current = lastSent.chatId;
    mutation.mutate(lastSent.text);
  }

  return { send: mutation.mutate, sending: mutation.isPending, retryLast };
}
