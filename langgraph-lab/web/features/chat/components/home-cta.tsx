"use client";

import { useRouter } from "next/navigation";
import { MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useHasHydrated } from "@/features/auth/hooks/use-hydrated";
import { useAuthStore } from "@/features/auth/store/auth-store";

export function HomeCta() {
  const router = useRouter();
  const hydrated = useHasHydrated();
  const accessToken = useAuthStore((state) => state.accessToken);
  if (!hydrated) {
    return (
      <div className="flex items-center gap-3" aria-hidden="true">
        <Skeleton className="h-9 w-44 rounded-lg" />
        <Skeleton className="h-9 w-32 rounded-lg" />
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3">
      <Button
        type="button"
        onClick={() => router.push(accessToken ? "/chat" : "/register")}
      >
        <MessageSquarePlus />
        ابدأ المحادثة الآن
      </Button>
      {!accessToken && (
        <Button type="button" variant="outline" onClick={() => router.push("/login")}>
          تسجيل الدخول
        </Button>
      )}
    </div>
  );
}
