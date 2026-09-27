"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { useFormError } from "@/components/auth/use-form-error";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { api, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState<string | null>(null);
  const form = useFormError();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    form.clear();
    try {
      const result = await unwrap(
        api.POST("/api/v1/auth/password-reset/request", { body: { email } }),
      );
      setSent(result.message);
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
    } finally {
      setPending(false);
    }
  }

  return (
    <AuthCard
      title="Reset your password"
      subtitle="We will email you a single-use link valid for 30 minutes."
      footer={
        <Link href="/login" className="text-accent hover:underline">
          Back to sign in
        </Link>
      }
    >
      {sent ? (
        <Alert tone="success">{sent}</Alert>
      ) : (
        <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
          {form.formMessage && <Alert tone="error">{form.formMessage}</Alert>}
          <Field
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={form.field("email")}
          />
          <Button type="submit" loading={pending}>
            Send reset link
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
