import { Skeleton } from "@/components/ui/skeleton";

export function ConversationsSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="جارٍ تحميل المحادثات"
      className="flex min-h-0 flex-1 flex-col gap-1 overflow-hidden"
    >
      <span className="sr-only">جارٍ تحميل المحادثات…</span>
      <Skeleton className="h-9 w-full rounded-lg" />
      <div className="mt-1 flex flex-col gap-1">
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton
            key={index}
            className="h-9 w-full rounded-lg"
            style={{ opacity: 1 - index * 0.12 }}
          />
        ))}
      </div>
    </div>
  );
}
