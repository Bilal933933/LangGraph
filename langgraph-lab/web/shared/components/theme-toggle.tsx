"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "التحويل إلى الوضع الفاتح" : "التحويل إلى الوضع الداكن"}
      title={isDark ? "وضع فاتح" : "وضع داكن"}
    >
      {isDark ? <Sun /> : <Moon />}
    </Button>
  );
}
