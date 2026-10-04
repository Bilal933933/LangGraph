"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createConversation, postConversationMessage } from "../lib/chat-api";
import { useChatStore } from "../store/chat-store";
import { conversationKey, conversationsKey } from "./use-conversations";

type SendInput = { text: string; conversationId: number | null };

export function useSendMessage(pageConversationId: number | null) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({ text, conversationId }: SendInput) => {
      let targetId = conversationId;
      if (targetId === null) {
        const created = await createConversation();
        targetId = created.id;
        queryClient.invalidateQueries({ queryKey: conversationsKey });
      }
      useChatStore.getState().setLastSent({ conversationId: targetId, text });
      const reply = await postConversationMessage(targetId, text);
      return { conversationId: targetId, reply };
    },
    onSuccess: ({ conversationId: targetId }) => {
      useChatStore.getState().setLastSent(null);
      queryClient.invalidateQueries({
        queryKey: conversationKey(targetId),
      });
      queryClient.invalidateQueries({ queryKey: conversationsKey });
      if (pageConversationId === null) router.push(`/chat/${targetId}`);
    },
    onError: (error) => {
      const message =
        error instanceof Error ? error.message : "حدث خطأ غير متوقع.";
      toast.error("تعذر إرسال الرسالة", {
        description: message,
        action: {
          label: "إعادة المحاولة",
          onClick: () => retryLast(),
        },
      });
    },
  });

  function send(text: string) {
    mutation.mutate({ text, conversationId: pageConversationId });
  }

  function retryLast() {
    const lastSent = useChatStore.getState().lastSent;
    if (!lastSent || mutation.isPending) return;
    if (pageConversationId === null) {
      router.push(`/chat/${lastSent.conversationId}`);
    }
    mutation.mutate({ text: lastSent.text, conversationId: lastSent.conversationId });
  }

  return { send, sending: mutation.isPending, retryLast };
}
