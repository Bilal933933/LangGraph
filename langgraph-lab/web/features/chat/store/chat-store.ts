import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { LastSent } from "../types";

type ChatUiState = {
  lastSent: LastSent;
  sidebarOpen: boolean;
  setLastSent: (value: LastSent) => void;
  setSidebarOpen: (open: boolean) => void;
};

export const useChatStore = create<ChatUiState>()(
  persist(
    (set) => ({
      lastSent: null,
      sidebarOpen: true,
      setLastSent: (value) => set({ lastSent: value }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: "langgraph-chat-ui",
      partialize: (state) => ({
        lastSent: state.lastSent,
        sidebarOpen: state.sidebarOpen,
      }),
    },
  ),
);
