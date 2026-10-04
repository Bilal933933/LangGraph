"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSession } from "../hooks/use-auth";
import { useHasHydrated } from "../hooks/use-hydrated";
import { AuthFormSkeleton } from "./auth-form-skeleton";

function CheckingSession() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6">
      <AuthFormSkeleton />
    </main>
  );
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const hydrated = useHasHydrated();
  const { status } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (hydrated && status === "out") {
      router.replace(`/login?next=${encodeURIComponent(pathname ?? "/chat")}`);
    }
  }, [hydrated, status, router, pathname]);

  if (!hydrated || status === "loading") return <CheckingSession />;
  if (status === "out") return <CheckingSession />;
  return <>{children}</>;
}
