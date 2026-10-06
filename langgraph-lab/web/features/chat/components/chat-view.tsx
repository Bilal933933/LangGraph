"use client";

import { useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStreamMessage } from "../hooks/use-stream-message";
import { useChatStore } from "../store/chat-store";
import {
  useConversationDetail,
  useConversations,
} from "../hooks/use-conversations";
import type { ChatMessage } from "../types";
import { AppSidebar } from "./app-sidebar";
import { ClarificationDialog } from "./clarification-dialog";
import { GreetingHero } from "./greeting-hero";
import { MessageComposer } from "./message-composer";
import { MessageList } from "./message-list";
import { MessagesSkeleton } from "./messages-skeleton";

const MAX_LENGTH = 4000;

function toUiMessages(
  messages: { id: number; role: "user" | "assistant"; content: string; created_at: string | null }[],
): ChatMessage[] {
  return messages.map((message) => ({
    id: `msg-${message.id}`,
    role: message.role,
    text: message.content,
    createdAt: message.created_at ? Date.parse(message.created_at) : 0,
  }));
}

export function ChatView({ conversationId }: { conversationId: number | null }) {
  const router = useRouter();
  const sidebarOpen = useChatStore((state) => state.sidebarOpen);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);
  const { data: chats = [] } = useConversations();
  const detail = useConversationDetail(conversationId);
  const { send, sending, retryLast } = useStreamMessage(conversationId);
  const streamingText = useChatStore((state) => state.streamingText);
  const streamStage = useChatStore((state) => state.streamStage);
  const [draft, setDraft] = useState("");
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const activeChat = chats.find((chat) => chat.id === conversationId);
  const baseMessages = detail.data ? toUiMessages(detail.data.messages) : [];
  const messages =
    streamingText.length > 0
      ? [
          ...baseMessages,
          {
            id: "streaming",
            role: "assistant" as const,
            text: streamingText,
            createdAt: 0,
          },
        ]
      : baseMessages;
  const showDetailSkeleton = conversationId !== null && detail.isPending;
  const isEmpty = messages.length === 0 && !sending && !detail.isPending;

  function submit(text: string) {
    const clean = text.trim().slice(0, MAX_LENGTH);
    if (!clean || sending) return;
    setDraft("");
    send(clean);
  }

  if (!mounted) {
    return (
      <div className="flex h-dvh items-center justify-center text-sm text-muted-foreground">
        جارٍ التحميل…
      </div>
    );
  }

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b border-border px-4 py-2.5">
          {!sidebarOpen && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => setSidebarOpen(true)}
              aria-label="فتح القائمة"
            >
              <PanelRightOpen />
            </Button>
          )}
          <h1 className="truncate text-sm font-medium">
            {activeChat?.title || detail.data?.title || "محادثة جديدة"}
          </h1>
        </header>

        {detail.isError ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-sm text-muted-foreground">
            تعذر تحميل المحادثة — ربما حُذفت.
            <Button type="button" variant="outline" onClick={() => router.push("/chat")}>
              محادثة جديدة
            </Button>
          </div>
        ) : showDetailSkeleton ? (
          <div className="min-h-0 flex-1 overflow-y-auto">
            <MessagesSkeleton count={3} />
          </div>
        ) : isEmpty ? (
          <GreetingHero onPick={submit} />
        ) : (
          <MessageList
            messages={messages}
            sending={sending && streamingText.length === 0}
            stage={streamStage}
            onRetry={retryLast}
          />
        )}

        <MessageComposer
          draft={draft}
          onDraftChange={setDraft}
          onSubmit={() => submit(draft)}
          sending={sending}
          maxLength={MAX_LENGTH}
        />
        <ClarificationDialog onSubmit={submit} />
      </div>
    </div>
  );
}
