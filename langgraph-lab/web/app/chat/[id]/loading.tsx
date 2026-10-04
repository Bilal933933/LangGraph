import { Skeleton } from "@/components/ui/skeleton";
import { ConversationsSkeleton } from "@/features/chat/components/conversations-skeleton";
import { MessagesSkeleton } from "@/features/chat/components/messages-skeleton";

export default function ConversationLoading() {
  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background">
      <aside className="flex h-full w-72 shrink-0 flex-col gap-2 border-e border-border bg-muted/40 p-3">
        <Skeleton className="h-7 w-2/3" />
        <Skeleton className="h-9 w-full rounded-lg" />
        <ConversationsSkeleton rows={5} />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="border-b border-border px-4 py-2.5">
          <Skeleton className="h-5 w-48" />
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <MessagesSkeleton count={3} />
        </div>
        <div className="px-4 pb-4">
          <Skeleton className="mx-auto h-12 w-full max-w-3xl rounded-2xl" />
        </div>
      </div>
    </div>
  );
}
