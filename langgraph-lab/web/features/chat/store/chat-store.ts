import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Clarification, LastSent } from "../types";

type ChatUiState = {
  lastSent: LastSent;
  sidebarOpen: boolean;
  clarification: Clarification | null;
  streamingText: string;
  streamStage: string | null;
  setLastSent: (value: LastSent) => void;
  setSidebarOpen: (open: boolean) => void;
  setClarification: (value: Clarification | null) => void;
  setStreamingText: (value: string) => void;
  setStreamStage: (value: string | null) => void;
};

export const useChatStore = create<ChatUiState>()(
  persist(
    (set) => ({
      lastSent: null,
      sidebarOpen: true,
      clarification: null,
      streamingText: "",
      streamStage: null,
      setLastSent: (value) => set({ lastSent: value }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setClarification: (value) => set({ clarification: value }),
      setStreamingText: (value) => set({ streamingText: value }),
      setStreamStage: (value) => set({ streamStage: value }),
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
