import { RequireAuth } from "@/features/auth/components/require-auth";
import { ChatView } from "@/features/chat/components/chat-view";

export default function NewChatPage() {
  return (
    <main className="h-dvh w-full">
      <RequireAuth>
        <ChatView conversationId={null} />
      </RequireAuth>
    </main>
  );
}
