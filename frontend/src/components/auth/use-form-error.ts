"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api/errors";

/** Tracks the last API error of a form and exposes per-field messages. */
export function useFormError() {
  const [error, setError] = useState<ApiError | Error | null>(null);
  return {
    error,
    setError,
    clear: () => setError(null),
    field: (name: string) => (error instanceof ApiError ? error.fieldError(name) : undefined),
    formMessage:
      error instanceof ApiError
        ? error.fieldErrors.length > 0
          ? undefined
          : error.userMessage
        : error
          ? "Something went wrong. Please try again."
          : undefined,
  };
}
