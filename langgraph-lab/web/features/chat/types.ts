export type ChatRole = "user" | "assistant" | "error";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  createdAt: number;
};

export type ServerChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string | null;
};

export type ConversationItem = {
  id: number;
  title: string;
  message_count: number;
  last_message: string;
  updated_at: string | null;
};

export type ConversationDetail = {
  id: number;
  title: string;
  messages: ServerChatMessage[];
};

export type LastSent = {
  conversationId: number;
  text: string;
} | null;
