import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const ROWS = [
  { align: "start", widths: ["w-3/4", "w-1/2"] },
  { align: "stretch", widths: ["w-full", "w-11/12", "w-2/3"] },
  { align: "start", widths: ["w-2/3"] },
] as const;

export function MessagesSkeleton({ count = 3 }: { count?: number }) {
  const rows = Array.from({ length: count }, (_, index) => ROWS[index % ROWS.length]);
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="جارٍ تحميل الرسائل"
      className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6"
    >
      <span className="sr-only">جارٍ تحميل الرسائل…</span>
      {rows.map((row, index) => (
        <div
          key={index}
          className={cn(
            "flex w-full flex-col gap-2",
            row.align === "start" ? "items-start" : "items-stretch",
          )}
        >
          {row.widths.map((width, line) => (
            <Skeleton key={line} className={`h-4 rounded-full ${width}`} />
          ))}
        </div>
      ))}
    </div>
  );
}
