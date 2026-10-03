"use client";

import { useState, useSyncExternalStore } from "react";
import { PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSendMessage } from "../hooks/use-send-message";
import { useChatStore } from "../store/chat-store";
import { AppSidebar } from "./app-sidebar";
import { GreetingHero } from "./greeting-hero";
import { MessageComposer } from "./message-composer";
import { MessageList } from "./message-list";

const MAX_LENGTH = 4000;

export function ChatView() {
  const chats = useChatStore((state) => state.chats);
  const activeChatId = useChatStore((state) => state.activeChatId);
  const sidebarOpen = useChatStore((state) => state.sidebarOpen);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);
  const { send, sending, retryLast } = useSendMessage();
  const [draft, setDraft] = useState("");
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const activeChat = chats.find((chat) => chat.id === activeChatId);
  const messages = activeChat?.messages ?? [];
  const isEmpty = messages.length === 0 && !sending;

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
            {activeChat?.title ?? "مساعد البحث الذكي"}
          </h1>
        </header>

        {isEmpty ? (
          <GreetingHero onPick={submit} />
        ) : (
          <MessageList
            messages={messages}
            sending={sending}
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
      </div>
    </div>
  );
}
