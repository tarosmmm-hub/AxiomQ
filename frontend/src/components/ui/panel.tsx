import type { ReactNode } from "react";

import { cn } from "./cn";

export function Panel({
  title,
  actions,
  children,
  className,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-lg border border-line bg-surface", className)}>
      {(title || actions) && (
        <header className="flex h-10 items-center justify-between border-b border-line px-4">
          <h2 className="text-[11px] font-semibold tracking-wider text-muted uppercase">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-start gap-1 py-6">
      <p className="text-sm font-medium text-fg">{title}</p>
      <p className="max-w-md text-sm text-muted">{description}</p>
    </div>
  );
}
