export type ChatRole = "user" | "assistant" | "error";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  createdAt: number;
  sources?: ChatSource[];
};

export type ChatSource = {
  title: string;
  subject: string;
  lesson: string;
  text: string;
};

export type SendMessageResult = {
  reply: string;
  sources: ChatSource[];
  clarification: Clarification | null;
};

export type Clarification = {
  kind: string;
  missing: string[];
  suggestions: Record<string, string[]>;
  profile_empty: boolean;
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
