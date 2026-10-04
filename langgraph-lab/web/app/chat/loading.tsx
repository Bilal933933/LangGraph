import { Skeleton } from "@/components/ui/skeleton";
import { ConversationsSkeleton } from "@/features/chat/components/conversations-skeleton";

export default function NewChatLoading() {
  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background">
      <aside className="flex h-full w-72 shrink-0 flex-col gap-2 border-e border-border bg-muted/40 p-3">
        <Skeleton className="h-7 w-2/3" />
        <Skeleton className="h-9 w-full rounded-lg" />
        <ConversationsSkeleton rows={5} />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col items-center justify-center gap-4 px-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 max-w-full" />
        <Skeleton className="h-12 w-full max-w-3xl rounded-2xl" />
      </div>
    </div>
  );
}
