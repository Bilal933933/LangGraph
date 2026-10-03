"use client";

const SUGGESTIONS = [
  { title: "من أنت؟", hint: "تعرف على المساعد" },
  { title: "ما هو LangGraph؟", hint: "اشرح باختصار" },
  { title: "اشرح useEffect", hint: "مع مثال عملي" },
  { title: "ما الفرق بين Chain و Graph؟", hint: "في تطبيقات الذكاء الاصطناعي" },
] as const;

export function GreetingHero({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-6 px-4">
      <h2 className="bg-gradient-to-l from-primary via-foreground to-muted-foreground bg-clip-text text-center text-3xl font-semibold text-transparent">
        مرحباً، كيف أساعدك اليوم؟
      </h2>
      <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion.title}
            type="button"
            onClick={() => onPick(suggestion.title)}
            className="flex flex-col gap-1 rounded-2xl border border-border bg-card px-4 py-3 text-start transition-colors hover:bg-muted/60"
          >
            <span className="text-sm font-medium">{suggestion.title}</span>
            <span className="text-xs text-muted-foreground">
              {suggestion.hint}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
