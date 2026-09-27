import type { ReactNode } from "react";

import { cn } from "./cn";

type Tone = "neutral" | "accent" | "positive" | "negative" | "warning";

const tones: Record<Tone, string> = {
  neutral: "bg-raised text-muted border-line",
  accent: "bg-accent-soft text-accent border-transparent",
  positive: "bg-positive-soft text-positive border-transparent",
  negative: "bg-negative-soft text-negative border-transparent",
  warning: "bg-warning-soft text-warning border-transparent",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded border px-1.5 font-mono text-[10px] font-semibold tracking-wider uppercase",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}
