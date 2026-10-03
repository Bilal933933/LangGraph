"use client";

export function TypingIndicator() {
  return (
    <div
      aria-label="المساعد يكتب الآن"
      className="flex items-center gap-1 self-end rounded-lg bg-muted px-3 py-3"
    >
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
