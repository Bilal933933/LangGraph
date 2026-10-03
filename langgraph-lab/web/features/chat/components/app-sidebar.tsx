"use client";

import { MessageSquarePlus, PanelRightClose, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import { useChatStore } from "../store/chat-store";
import { cn } from "@/lib/utils";

export function AppSidebar() {
  const chats = useChatStore((state) => state.chats);
  const activeChatId = useChatStore((state) => state.activeChatId);
  const sidebarOpen = useChatStore((state) => state.sidebarOpen);
  const newChat = useChatStore((state) => state.newChat);
  const selectChat = useChatStore((state) => state.selectChat);
  const deleteChat = useChatStore((state) => state.deleteChat);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);

  if (!sidebarOpen) return null;

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col gap-2 border-e border-border bg-muted/40 p-3">
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={() => setSidebarOpen(false)}
          aria-label="إغلاق القائمة"
        >
          <PanelRightClose />
        </Button>
        <span className="text-sm font-semibold">مساعد البحث الذكي</span>
      </div>

      <Button type="button" onClick={newChat} className="justify-start gap-2">
        <MessageSquarePlus />
        محادثة جديدة
      </Button>

      <nav
        aria-label="المحادثات"
        className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto"
      >
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={cn(
              "group flex items-center gap-1 rounded-lg",
              chat.id === activeChatId && "bg-muted",
            )}
          >
            <button
              type="button"
              onClick={() => selectChat(chat.id)}
              title={chat.title}
              className="flex-1 truncate px-3 py-2 text-start text-sm"
            >
              {chat.title}
            </button>
            <button
              type="button"
              onClick={() => deleteChat(chat.id)}
              aria-label={`حذف ${chat.title}`}
              className="rounded-md p-1.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive focus-visible:opacity-100"
            >
              <Trash2 className="size-4" />
            </button>
          </div>
        ))}
      </nav>

      <div className="flex items-center justify-between border-t border-border pt-2">
        <span className="text-xs text-muted-foreground">
          Gemini عبر LangGraph
        </span>
        <ThemeToggle />
      </div>
    </aside>
  );
}
