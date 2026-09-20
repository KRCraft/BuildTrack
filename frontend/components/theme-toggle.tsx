"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Toggle theme"
        aria-hidden
        className="grid h-9 w-9 place-items-center rounded-lg border border-[#e5e8e3] dark:border-[#2a3a33] bg-white dark:bg-[#1a2e26] text-[#65716a] dark:text-[#a1aea8]"
        disabled
      >
        <Sun size={16} aria-hidden="true" className="opacity-0" />
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="grid h-9 w-9 place-items-center rounded-lg border border-[#e5e8e3] dark:border-[#2a3a33] bg-white dark:bg-[#1a2e26] text-[#65716a] hover:bg-[#f5f7f4] hover:text-ink dark:text-[#a1aea8] dark:hover:bg-[#1e2e28] dark:hover:text-[#eaf3ee] transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40"
    >
      {isDark ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
    </button>
  );
}
