import { useId, type InputHTMLAttributes } from "react";

import { cn } from "./cn";

export interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string | undefined;
}

export function Field({ label, hint, error, className, id, ...props }: FieldProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={inputId} className="text-xs font-medium text-muted">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          "h-9 rounded-md border bg-surface px-3 text-sm text-fg placeholder:text-subtle",
          "transition-colors focus:border-accent focus:outline-none",
          error ? "border-negative" : "border-line hover:border-line-strong",
        )}
        {...props}
      />
      {error ? (
        <p id={`${inputId}-error`} className="text-xs text-negative">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-xs text-subtle">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
