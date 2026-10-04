import { useAuthStore } from "@/features/auth/store/auth-store";
import type { ConversationDetail, ConversationItem } from "../types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().accessToken;
  if (!token) throw new Error("يلزم تسجيل الدخول.");
  return { Authorization: `Bearer ${token}` };
}

export async function listConversations(): Promise<ConversationItem[]> {
  const response = await fetch(`${API_BASE}/conversations`, {
    headers: authHeaders(),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationItem[];
}

export async function createConversation(
  title = "",
): Promise<ConversationItem> {
  const response = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ title }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationItem;
}

export async function getConversation(
  id: number,
): Promise<ConversationDetail> {
  const response = await fetch(`${API_BASE}/conversations/${id}`, {
    headers: authHeaders(),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationDetail;
}

export async function deleteConversation(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/conversations/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(data, response.status));
  }
}

export async function postConversationMessage(
  id: number,
  message: string,
): Promise<string> {
  const response = await fetch(`${API_BASE}/conversations/${id}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  if (!isMessageReply(data)) throw new Error("رد غير صالح من السيرفر.");
  return data.reply;
}

function isMessageReply(data: unknown): data is { reply: string } {
  return (
    typeof data === "object" &&
    data !== null &&
    "reply" in data &&
    typeof (data as { reply: unknown }).reply === "string"
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
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.length > 0) return detail;
  }
  return `خطأ ${status}`;
}
