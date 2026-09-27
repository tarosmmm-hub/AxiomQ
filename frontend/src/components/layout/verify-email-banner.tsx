"use client";

import { useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { api, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

export function VerifyEmailBanner({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");

  async function resend() {
    setState("sending");
    try {
      await unwrap(api.POST("/api/v1/auth/email/resend"));
      setState("sent");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.userMessage : "Could not send the email.");
      setState("error");
    }
  }

  return (
    <Alert tone="warning" className="flex flex-wrap items-center justify-between gap-3">
      <span>
        Verify <strong className="font-medium">{email}</strong> to run backtests.{" "}
        {state === "sent" && "A new link is on its way."}
        {state === "error" && message}
      </span>
      {state !== "sent" && (
        <Button size="sm" variant="secondary" onClick={resend} loading={state === "sending"}>
          Resend link
        </Button>
      )}
    </Alert>
  );
}
