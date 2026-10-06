import { authedFetch } from "@/features/auth/lib/authed-fetch";
import type {
  ChatSource,
  Clarification,
  ConversationDetail,
  ConversationItem,
  SendMessageResult,
} from "../types";

export async function listConversations(): Promise<ConversationItem[]> {
  const response = await authedFetch(`/conversations`);
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationItem[];
}

export async function createConversation(
  title = "",
): Promise<ConversationItem> {
  const response = await authedFetch(`/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationItem;
}

export async function getConversation(
  id: number,
): Promise<ConversationDetail> {
  const response = await authedFetch(`/conversations/${id}`);
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  return data as ConversationDetail;
}

export async function deleteConversation(id: number): Promise<void> {
  const response = await authedFetch(`/conversations/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    throw new Error(extractErrorMessage(data, response.status));
  }
}

export async function postConversationMessage(
  id: number,
  message: string,
): Promise<SendMessageResult> {
  const response = await authedFetch(`/conversations/${id}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new Error(extractErrorMessage(data, response.status));
  if (!isMessageReply(data)) throw new Error("رد غير صالح من السيرفر.");
  const reply = data as { reply: string; clarification?: unknown };
  return { reply: reply.reply, sources: extractSources(data), clarification: extractClarification(reply) };
}

export function extractClarification(data: { clarification?: unknown }): Clarification | null {
  if (typeof data.clarification !== "object" || data.clarification === null) return null;
  const item = data.clarification as Record<string, unknown>;
  if (!Array.isArray(item.missing)) return null;
  const missing = item.missing.filter((f): f is string => typeof f === "string");
  if (missing.length === 0) return null;
  const suggestions: Record<string, string[]> =
    typeof item.suggestions === "object" && item.suggestions !== null
      ? Object.fromEntries(
          Object.entries(item.suggestions as Record<string, unknown>).map(([key, value]) => [
            key,
            Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [],
          ]),
        )
      : {};
  return {
    kind: typeof item.kind === "string" ? item.kind : "plan",
    missing,
    suggestions,
    profile_empty: item.profile_empty === true,
  };
}

export function extractSources(data: { reply: string; sources?: unknown }): ChatSource[] {
  if (!Array.isArray(data.sources)) return [];
  return data.sources
    .filter(
      (item): item is Record<string, unknown> =>
        typeof item === "object" && item !== null,
    )
    .map((item) => ({
      title: typeof item.title === "string" ? item.title : "",
      subject: typeof item.subject === "string" ? item.subject : "",
      lesson: typeof item.lesson === "string" ? item.lesson : "",
      text: typeof item.text === "string" ? item.text : "",
    }))
    .filter((source) => source.title || source.lesson || source.text);
}

function isMessageReply(data: unknown): data is { reply: string } {
  return (
    typeof data === "object" &&
    data !== null &&
    "reply" in data &&
    typeof (data as { reply: unknown }).reply === "string"
  );
}

export function extractErrorMessage(data: unknown, status: number): string {
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
