"use client";

const STAGE_LABELS: Record<string, string> = {
  extract: "يستخرج التفاصيل…",
  plan_extract: "يستخرج تفاصيل الخطة…",
  retrieve: "يبحث في الكتب…",
  answer: "يكتب الرد…",
  quiz_agent: "يولد الاختبار…",
  quiz_tools: "يجلب الدروس…",
  plan_section: "يكتب أقسام الخطة…",
};

export function TypingIndicator({ stage }: { stage?: string | null }) {
  const label = (stage && STAGE_LABELS[stage]) || "المساعد يكتب الآن";
  return (
    <div
      aria-label={label}
      className="flex items-center gap-2 self-end rounded-lg bg-muted px-3 py-3"
    >
      <span className="text-xs text-muted-foreground">{label}</span>
      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className="size-1.5 animate-bounce rounded-full bg-muted-foreground"
          style={{ animationDelay: `${index * 150}ms` }}
        />
      ))}
    </div>
  );
}
