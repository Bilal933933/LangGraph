import { Skeleton } from "@/components/ui/skeleton";

export function AuthFormSkeleton() {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="جارٍ تحميل النموذج"
      className="flex w-full max-w-sm flex-col gap-4"
    >
      <span className="sr-only">جارٍ تحميل النموذج…</span>
      <Skeleton className="h-7 w-2/3" />
      <Skeleton className="h-10 w-full rounded-lg" />
      <Skeleton className="h-10 w-full rounded-lg" />
      <Skeleton className="h-9 w-full rounded-lg" />
    </div>
  );
}
