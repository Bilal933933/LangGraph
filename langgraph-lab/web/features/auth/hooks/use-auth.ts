"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { fetchMe, loginApi, refreshApi, registerApi } from "../lib/auth-api";
import { resolveNextPath } from "../lib/auth-validators";
import type { AuthUser, LoginInput, RegisterInput } from "../types";
import { useAuthStore } from "../store/auth-store";

function nextAfterAuth(): string {
  if (typeof window === "undefined") return "/";
  return resolveNextPath(new URLSearchParams(window.location.search).get("next"));
}

export function useRegister() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RegisterInput) => registerApi(input),
    onSuccess: async (tokens) => {
      const user = await fetchMe(tokens.access_token);
      useAuthStore.getState().setSession(tokens, user);
      queryClient.setQueryData(["me"], user);
      toast.success("تم إنشاء الحساب");
      router.push(nextAfterAuth());
    },
    onError: (error) => {
      toast.error("تعذر التسجيل", {
        description: error instanceof Error ? error.message : "حاول مجددًا.",
      });
    },
  });
}

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: LoginInput) => loginApi(input),
    onSuccess: async (tokens) => {
      const user = await fetchMe(tokens.access_token);
      useAuthStore.getState().setSession(tokens, user);
      queryClient.setQueryData(["me"], user);
      toast.success("تم تسجيل الدخول");
      router.push(nextAfterAuth());
    },
    onError: (error) => {
      toast.error("تعذر الدخول", {
        description: error instanceof Error ? error.message : "تحقق من البيانات.",
      });
    },
  });
}

export function useMe() {
  const accessToken = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["me"],
    queryFn: () => {
      if (!accessToken) throw new Error("يلزم تسجيل الدخول.");
      return fetchMe(accessToken);
    },
    enabled: accessToken !== null,
    retry: false,
  });
}

export type SessionStatus = "loading" | "in" | "out";

export function useSession(): { status: SessionStatus; user: AuthUser | null } {
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const query = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      if (!accessToken) throw new Error("out");
      try {
        return await fetchMe(accessToken);
      } catch {
        if (!refreshToken) {
          useAuthStore.getState().clear();
          throw new Error("out");
        }
        try {
          const tokens = await refreshApi(refreshToken);
          const user = await fetchMe(tokens.access_token);
          useAuthStore.getState().setSession(tokens, user);
          return user;
        } catch {
          useAuthStore.getState().clear();
          throw new Error("out");
        }
      }
    },
    enabled: accessToken !== null,
    retry: false,
    staleTime: 60_000,
  });
  if (accessToken === null) return { status: "out", user: null };
  if (query.isPending) return { status: "loading", user: null };
  if (query.isSuccess) return { status: "in", user: query.data };
  return { status: "out", user: null };
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  return () => {
    useAuthStore.getState().clear();
    queryClient.removeQueries({ queryKey: ["me"] });
    router.push("/login");
  };
}
