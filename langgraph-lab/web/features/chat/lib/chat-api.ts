const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export async function postChat(message: string): Promise<string> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorMessage(data, response.status));
  }
  if (!isChatReply(data)) {
    throw new Error("رد غير صالح من السيرفر.");
  }
  return data.reply;
}

function isChatReply(data: unknown): data is { reply: string } {
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
