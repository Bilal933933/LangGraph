"use client";

import { useSyncExternalStore } from "react";
import { useAuthStore } from "../store/auth-store";

export function useHasHydrated(): boolean {
  return useSyncExternalStore(
    (onStoreChange) => useAuthStore.persist.onFinishHydration(onStoreChange),
    () => useAuthStore.persist.hasHydrated(),
    () => false,
  );
}
