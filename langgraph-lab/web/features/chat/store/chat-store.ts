import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Clarification, LastSent } from "../types";

type ChatUiState = {
  lastSent: LastSent;
  sidebarOpen: boolean;
  clarification: Clarification | null;
  setLastSent: (value: LastSent) => void;
  setSidebarOpen: (open: boolean) => void;
  setClarification: (value: Clarification | null) => void;
};

export const useChatStore = create<ChatUiState>()(
  persist(
    (set) => ({
      lastSent: null,
      sidebarOpen: true,
      clarification: null,
      setLastSent: (value) => set({ lastSent: value }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setClarification: (value) => set({ clarification: value }),
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
