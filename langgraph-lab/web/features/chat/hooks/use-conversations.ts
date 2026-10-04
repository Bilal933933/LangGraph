"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuthStore } from "@/features/auth/store/auth-store";
import {
  deleteConversation,
  getConversation,
  listConversations,
} from "../lib/chat-api";

export const conversationsKey = ["conversations"] as const;
export const conversationKey = (id: number | null) =>
  ["conversation", id] as const;

function isAuthed(): boolean {
  return useAuthStore.getState().accessToken !== null;
}

export function useConversations() {
  return useQuery({
    queryKey: conversationsKey,
    queryFn: listConversations,
    enabled: isAuthed(),
    retry: false,
  });
}

export function useConversationDetail(id: number | null) {
  return useQuery({
    queryKey: conversationKey(id),
    queryFn: () => {
      if (id === null) throw new Error("لا محادثة مختارة.");
      return getConversation(id);
    },
    enabled: isAuthed() && id !== null,
    retry: false,
  });
}

export function useDeleteConversation() {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteConversation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: conversationsKey });
      queryClient.removeQueries({ queryKey: conversationKey(id) });
      if (pathname === `/chat/${id}`) router.push("/chat");
      toast.success("تم حذف المحادثة");
    },
    onError: (error) => {
      toast.error("تعذر حذف المحادثة", {
        description: error instanceof Error ? error.message : "حاول مجددًا.",
      });
    },
  });
}
