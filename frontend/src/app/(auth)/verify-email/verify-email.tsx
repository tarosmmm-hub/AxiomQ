"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { api, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

type State = { kind: "pending" } | { kind: "ok" } | { kind: "error"; message: string };

export function VerifyEmail({ token }: { token: string | undefined }) {
  const [state, setState] = useState<State>(
    token
      ? { kind: "pending" }
      : { kind: "error", message: "This verification link is incomplete." },
  );
  const started = useRef(false);

  useEffect(() => {
    // Tokens are single-use: guard against the double effect run in React strict mode.
    if (!token || started.current) return;
    started.current = true;
    unwrap(api.POST("/api/v1/auth/email/verify", { body: { token } }))
      .then(() => setState({ kind: "ok" }))
      .catch((error: unknown) =>
        setState({
          kind: "error",
          message: error instanceof ApiError ? error.title : "Verification failed.",
        }),
      );
  }, [token]);

  return (
    <AuthCard title="Email verification">
      {state.kind === "pending" && (
        <p className="flex items-center gap-2 text-sm text-muted">
          <Spinner /> Verifying…
        </p>
      )}
      {state.kind === "ok" && <Alert tone="success">Your email address is verified.</Alert>}
      {state.kind === "error" && <Alert tone="error">{state.message}</Alert>}
      {state.kind !== "pending" && (
        <Link href="/dashboard" className="mt-4 inline-block text-sm text-accent hover:underline">
          Go to dashboard
        </Link>
      )}
    </AuthCard>
  );
}
