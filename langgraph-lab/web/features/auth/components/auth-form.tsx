"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { validateEmail, validatePassword } from "../lib/auth-validators";

type Props = {
  mode: "login" | "register";
  pending: boolean;
  onSubmit: (email: string, password: string) => void;
};

export function AuthForm({ mode, pending, onSubmit }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const emailError = validateEmail(email);
    if (emailError) {
      setError(emailError);
      return;
    }
    const passwordError = mode === "register" ? validatePassword(password) : null;
    if (passwordError) {
      setError(passwordError);
      return;
    }
    setError(null);
    onSubmit(email.trim(), password);
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-3">
      <h1 className="text-xl font-semibold">
        {mode === "login" ? "تسجيل الدخول" : "إنشاء حساب"}
      </h1>
      <Input
        type="email"
        placeholder="البريد الإلكتروني"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        dir="ltr"
      />
      <Input
        type="password"
        placeholder="كلمة السر (8 أحرف على الأقل)"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        dir="ltr"
      />
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      <Button type="submit" disabled={pending}>
        {pending ? "جارٍ..." : mode === "login" ? "دخول" : "تسجيل"}
      </Button>
    </form>
  );
}
