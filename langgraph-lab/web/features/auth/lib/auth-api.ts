import type { AuthUser, LoginInput, RegisterInput, TokenPair } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export async function registerApi(input: RegisterInput): Promise<TokenPair> {
  return postJson<TokenPair>("/auth/register", input, 201);
}

export async function loginApi(input: LoginInput): Promise<TokenPair> {
  return postJson<TokenPair>("/auth/login", input, 200);
}

export async function refreshApi(refreshToken: string): Promise<TokenPair> {
  return postJson<TokenPair>("/auth/refresh", { refresh_token: refreshToken }, 200);
}

export async function fetchMe(accessToken: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  if (!isAuthUser(data)) throw new Error("رد غير صالح من السيرفر.");
  return data;
}

async function postJson<T>(path: string, body: unknown, expected: number): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data: unknown = await response.json().catch(() => null);
  if (response.status !== expected || !response.ok) {
    throw new Error(extractErrorMessage(data, response.status));
  }
  return data as T;
}

function isAuthUser(data: unknown): data is AuthUser {
  return (
    typeof data === "object" &&
    data !== null &&
    "email" in data &&
    typeof (data as { email: unknown }).email === "string"
  );
}

function extractErrorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null && "error" in data) {
    const err = (data as { error: unknown }).error;
    if (typeof err === "object" && err !== null && "message" in err) {
      const msg = (err as { message: unknown }).message;
      if (typeof msg === "string" && msg.length > 0) return msg;
    }
  }
  return `خطأ ${status}`;
}
