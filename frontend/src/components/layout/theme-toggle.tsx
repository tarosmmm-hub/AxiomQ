"use client";

import { useSyncExternalStore } from "react";

import { applyThemePreference, readThemePreference, type ThemePreference } from "@/lib/theme";
import { cn } from "@/components/ui/cn";

const OPTIONS: Array<{ value: ThemePreference; label: string }> = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "Auto" },
];

let listeners: Array<() => void> = [];
const subscribe = (fn: () => void) => {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
};

export function ThemeToggle() {
  const current = useSyncExternalStore(subscribe, readThemePreference, () => "system" as const);
  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className="inline-flex rounded-md border border-line bg-surface p-0.5"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={current === option.value}
          onClick={() => {
            applyThemePreference(option.value);
            listeners.forEach((l) => l());
          }}
          className={cn(
            "h-6 rounded px-2 text-[11px] font-medium transition-colors",
            current === option.value ? "bg-raised text-fg" : "text-subtle hover:text-fg",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
