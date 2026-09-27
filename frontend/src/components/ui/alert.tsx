import type { ReactNode } from "react";

import { cn } from "./cn";

type Tone = "info" | "success" | "warning" | "error";

const tones: Record<Tone, string> = {
  info: "border-line bg-raised text-fg",
  success: "border-transparent bg-positive-soft text-positive",
  warning: "border-transparent bg-warning-soft text-warning",
  error: "border-transparent bg-negative-soft text-negative",
};

export function Alert({
  tone = "info",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn("rounded-md border px-3 py-2 text-sm", tones[tone], className)}
    >
      {children}
    </div>
  );
}
