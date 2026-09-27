"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { useFormError } from "@/components/auth/use-form-error";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { api, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

export function ResetPasswordForm({ token }: { token: string | undefined }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pending, setPending] = useState(false);
  const form = useFormError();

  if (!token) {
    return (
      <AuthCard title="Invalid link" subtitle="This password reset link is incomplete.">
        <Link href="/forgot-password" className="text-sm text-accent hover:underline">
          Request a new link
        </Link>
      </AuthCard>
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    form.clear();
    if (password !== confirm) {
      form.setError(
        new ApiError(422, {
          title: "Validation failed",
          errors: [{ field: "confirm", message: "Passwords do not match." }],
        }),
      );
      return;
    }
    setPending(true);
    try {
      await unwrap(
        api.POST("/api/v1/auth/password-reset/confirm", {
          body: { token: token as string, new_password: password },
        }),
      );
      router.replace("/login?notice=password-reset");
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
      setPending(false);
    }
  }

  return (
    <AuthCard title="Choose a new password" subtitle="All your active sessions will be signed out.">
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {form.formMessage && <Alert tone="error">{form.formMessage}</Alert>}
        <Field
          label="New password"
          type="password"
          autoComplete="new-password"
          required
          minLength={12}
          hint="At least 12 characters."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={form.field("password")}
        />
        <Field
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={form.field("confirm")}
        />
        <Button type="submit" loading={pending}>
          Update password
        </Button>
      </form>
    </AuthCard>
  );
}
