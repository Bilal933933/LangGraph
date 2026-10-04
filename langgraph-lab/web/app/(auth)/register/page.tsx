"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AuthForm } from "@/features/auth/components/auth-form";
import { AuthFormSkeleton } from "@/features/auth/components/auth-form-skeleton";
import { useRegister } from "@/features/auth/hooks/use-auth";
import { useHasHydrated } from "@/features/auth/hooks/use-hydrated";
import { resolveNextPath } from "@/features/auth/lib/auth-validators";
import { useAuthStore } from "@/features/auth/store/auth-store";

export default function RegisterPage() {
  const register = useRegister();
  const router = useRouter();
  const hydrated = useHasHydrated();
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    if (hydrated && accessToken) {
      const next =
        typeof window === "undefined"
          ? "/chat"
          : resolveNextPath(new URLSearchParams(window.location.search).get("next"));
      router.replace(next);
    }
  }, [hydrated, accessToken, router]);
  if (!hydrated) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
        <AuthFormSkeleton />
      </main>
    );
  }
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <AuthForm
        mode="register"
        pending={register.isPending}
        onSubmit={(email, password) => register.mutate({ email, password })}
      />
      <Link href="/login" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
        لديك حساب؟ سجل الدخول
      </Link>
    </main>
  );
}
