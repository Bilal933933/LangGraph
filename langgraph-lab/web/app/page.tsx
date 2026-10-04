import { HomeCta } from "@/features/chat/components/home-cta";

export default function Home() {
  return (
    <main className="flex min-h-dvh w-full flex-col items-center justify-center gap-6 bg-background px-6 text-center">
      <p className="text-sm text-muted-foreground">Gemini عبر LangGraph</p>
      <h1 className="max-w-2xl text-4xl font-bold tracking-tight">
        مساعد البحث الذكي للمعلم
      </h1>
      <p className="max-w-xl text-muted-foreground">
        اسأل، احصل على إجابات فورية، وأنشئ اختبارات جاهزة — مع سجل محادثات
        محفوظ يتذكر سياقك.
      </p>
      <HomeCta />
    </main>
  );
}
