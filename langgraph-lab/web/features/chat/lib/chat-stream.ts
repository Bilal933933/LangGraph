import { authedFetch } from "@/features/auth/lib/authed-fetch";
import {
  extractClarification,
  extractErrorMessage,
  extractSources,
} from "./chat-api";
import type { SendMessageResult } from "../types";

export type StreamHandlers = {
  onStage?: (node: string) => void;
  onProgress?: (node: string, phase: string) => void;
  onToken?: (text: string) => void;
  onDone?: (result: SendMessageResult) => void;
  onError?: (error: Error) => void;
};

type DonePayload = {
  reply?: unknown;
  sources?: unknown;
  clarification?: unknown;
};

function toError(value: unknown): Error {
  return value instanceof Error ? value : new Error("تعذر الاتصال بالسيرفر.");
}

/** يوزع إطار SSE واحد (event + data) على المعالجات. */
function dispatchFrame(frame: string, handlers: StreamHandlers): void {
  let event = "";
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event: ")) event = line.slice("event: ".length);
    else if (line.startsWith("data: ")) dataLines.push(line.slice("data: ".length));
  }
  if (dataLines.length === 0) return;
  let data: unknown = null;
  try {
    data = JSON.parse(dataLines.join("\n")) as unknown;
  } catch {
    return;
  }
  if (event === "stage" && typeof (data as { node?: unknown }).node === "string") {
    handlers.onStage?.((data as { node: string }).node);
  } else if (
    event === "token" &&
    (data as { node?: unknown }).node === "answer" &&
    typeof (data as { text?: unknown }).text === "string"
  ) {
    handlers.onToken?.((data as { text: string }).text);
  } else if (
    event === "progress" &&
    typeof (data as { node?: unknown }).node === "string" &&
    typeof (data as { phase?: unknown }).phase === "string"
  ) {
    handlers.onProgress?.(
      (data as { node: string }).node,
      (data as { phase: string }).phase,
    );
  } else if (event === "done") {
    const payload = data as DonePayload;
    if (typeof payload.reply !== "string") return;
    const reply: string = payload.reply;
    handlers.onDone?.({
      reply,
      sources: extractSources({ reply, sources: payload.sources }),
      clarification: extractClarification({ clarification: payload.clarification }),
    });
  } else if (event === "error") {
    const message =
      typeof (data as { message?: unknown }).message === "string"
        ? (data as { message: string }).message
        : "تعذر البث الآن.";
    handlers.onError?.(new Error(message));
  }
}

/** يبث رسالة محادثة: مراحل ← رموز ← إتمام (POST + قارئ fetch). */
export async function streamConversationMessage(
  id: number,
  message: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await authedFetch(`/conversations/${id}/messages/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal,
    });
  } catch (error) {
    handlers.onError?.(toError(error));
    return;
  }
  if (!response.ok || !response.body) {
    const data: unknown = await response.json().catch(() => null);
    handlers.onError?.(new Error(extractErrorMessage(data, response.status)));
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let cut = buffer.indexOf("\n\n");
      while (cut >= 0) {
        dispatchFrame(buffer.slice(0, cut), handlers);
        buffer = buffer.slice(cut + 2);
        cut = buffer.indexOf("\n\n");
      }
    }
    if (buffer.trim().length > 0) dispatchFrame(buffer, handlers);
  } catch (error) {
    handlers.onError?.(toError(error));
  } finally {
    reader.releaseLock();
  }
}
