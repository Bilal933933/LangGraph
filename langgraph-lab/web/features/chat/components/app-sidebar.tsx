"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { MessageSquarePlus, PanelRightClose, Trash2 } from "lucide-react";
import { DeleteDialog } from "@/components/shared/delete-dialog";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import { useChatStore } from "../store/chat-store";
import { ConversationsSkeleton } from "./conversations-skeleton";
import { cn } from "@/lib/utils";
import { useConversations, useDeleteConversation } from "../hooks/use-conversations";

export function AppSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const sidebarOpen = useChatStore((state) => state.sidebarOpen);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);
  const { data: chats = [], isPending } = useConversations();
  const removeChat = useDeleteConversation();
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);

  const pendingDelete = chats.find((chat) => chat.id === pendingDeleteId);

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

      <Button
        type="button"
        onClick={() => router.push("/chat")}
        className="justify-start gap-2"
      >
        <MessageSquarePlus />
        محادثة جديدة
      </Button>

      <nav
        aria-label="المحادثات"
        className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto"
      >
        {isPending ? (
          <ConversationsSkeleton rows={5} />
        ) : chats.length === 0 ? (
          <p className="px-3 py-2 text-sm text-muted-foreground">
            لا محادثات بعد — ابدأ واحدة جديدة.
          </p>
        ) : (
          chats.map((chat) => {
            const href = `/chat/${chat.id}`;
            const active = pathname === href;
            return (
              <div
                key={chat.id}
                className={cn(
                  "group flex items-center gap-1 rounded-lg",
                  active && "bg-muted",
                )}
              >
                <Link
                  href={href}
                  title={chat.title || "محادثة جديدة"}
                  className="flex-1 truncate px-3 py-2 text-start text-sm"
                >
                  {chat.title || "محادثة جديدة"}
                </Link>
                <button
                  type="button"
                  onClick={() => setPendingDeleteId(chat.id)}
                  aria-label={`حذف ${chat.title || "المحادثة"}`}
                  className="rounded-md p-1.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive focus-visible:opacity-100"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            );
          })
        )}
      </nav>

      <div className="flex items-center justify-between border-t border-border pt-2">
        <span className="text-xs text-muted-foreground">
          Gemini عبر LangGraph
        </span>
        <ThemeToggle />
      </div>

      <DeleteDialog
        open={pendingDeleteId !== null}
        title="حذف المحادثة؟"
        description={
          pendingDelete
            ? `سيتم حذف "${pendingDelete.title || "محادثة جديدة"}" وكل رسائلها نهائيًا.`
            : "سيتم حذف المحادثة وكل رسائلها نهائيًا."
        }
        confirming={removeChat.isPending}
        onOpenChange={(open) => {
          if (!open) setPendingDeleteId(null);
        }}
        onConfirm={() => {
          if (pendingDeleteId === null) return;
          removeChat.mutate(pendingDeleteId, {
            onSuccess: () => setPendingDeleteId(null),
          });
        }}
      />
    </aside>
  );
}
