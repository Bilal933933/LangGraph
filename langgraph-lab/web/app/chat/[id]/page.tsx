import { notFound } from "next/navigation";
import { RequireAuth } from "@/features/auth/components/require-auth";
import { ChatView } from "@/features/chat/components/chat-view";

export default async function ConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const conversationId = Number(id);
  if (!Number.isInteger(conversationId) || conversationId <= 0) notFound();

  return (
    <main className="h-dvh w-full">
      <RequireAuth>
        <ChatView conversationId={conversationId} />
      </RequireAuth>
    </main>
  );
}
