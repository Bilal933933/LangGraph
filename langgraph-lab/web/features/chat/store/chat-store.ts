import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Chat, ChatMessage, LastSent } from "../types";

type ChatState = {
  chats: Chat[];
  activeChatId: string | null;
  lastSent: LastSent;
  sidebarOpen: boolean;
  newChat: () => void;
  selectChat: (id: string) => void;
  deleteChat: (id: string) => void;
  pushMessage: (chatId: string, message: ChatMessage) => void;
  setLastSent: (value: LastSent) => void;
  setSidebarOpen: (open: boolean) => void;
};

function createChat(): Chat {
  const now = Date.now();
  return {
    id: `chat-${now.toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    title: "محادثة جديدة",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

const seed = createChat();

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      chats: [seed],
      activeChatId: seed.id,
      lastSent: null,
      sidebarOpen: true,
      newChat: () =>
        set((state) => {
          const chat = createChat();
          return {
            chats: [chat, ...state.chats],
            activeChatId: chat.id,
            lastSent: null,
          };
        }),
      selectChat: (id) => set({ activeChatId: id, lastSent: null }),
      deleteChat: (id) =>
        set((state) => {
          const chats = state.chats.filter((chat) => chat.id !== id);
          const next = chats.length > 0 ? chats : [createChat()];
          return {
            chats: next,
            activeChatId:
              state.activeChatId === id ? next[0].id : state.activeChatId,
            lastSent: null,
          };
        }),
      pushMessage: (chatId, message) =>
        set((state) => ({
          chats: state.chats.map((chat) =>
            chat.id === chatId
              ? {
                  ...chat,
                  messages: [...chat.messages, message],
                  title:
                    chat.messages.length === 0 && message.role === "user"
                      ? message.text.slice(0, 32)
                      : chat.title,
                  updatedAt: Date.now(),
                }
              : chat,
          ),
        })),
      setLastSent: (value) => set({ lastSent: value }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: "langgraph-chat",
      partialize: (state) => ({
        chats: state.chats,
        activeChatId: state.activeChatId,
      }),
    },
  ),
);

export function ensureActiveChatId(): string {
  const state = useChatStore.getState();
  const exists = state.chats.some((chat) => chat.id === state.activeChatId);
  if (exists && state.activeChatId) return state.activeChatId;
  state.newChat();
  const fresh = useChatStore.getState().activeChatId;
  if (!fresh) throw new Error("تعذر إنشاء محادثة.");
  return fresh;
}

export function createMessageId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}
