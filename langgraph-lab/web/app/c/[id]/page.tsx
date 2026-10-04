import { notFound, redirect } from "next/navigation";

// توافق خلفي: المسار القديم /c/[id] يُحوَّل للمسار الجديد /chat/[id].
export default async function LegacyConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const conversationId = Number(id);
  if (!Number.isInteger(conversationId) || conversationId <= 0) notFound();
  redirect(`/chat/${conversationId}`);
}
