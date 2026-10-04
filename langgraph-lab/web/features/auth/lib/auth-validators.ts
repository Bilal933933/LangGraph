export function validateEmail(email: string): string | null {
  const cleaned = email.trim().toLowerCase();
  if (!cleaned.includes("@") || cleaned.length < 3) return "البريد الإلكتروني غير صالح.";
  return null;
}

export function validatePassword(password: string): string | null {
  if (password.length < 8) return "كلمة السر 8 أحرف على الأقل.";
  return null;
}

export function resolveNextPath(value: string | null): string {
  if (value && value.startsWith("/") && !value.startsWith("//")) return value;
  return "/chat";
}
