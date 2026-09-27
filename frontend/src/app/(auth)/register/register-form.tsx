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

export function RegisterForm() {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const form = useFormError();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    form.clear();
    try {
      const result = await unwrap(
        api.POST("/api/v1/auth/register", {
          body: { email, password, display_name: displayName },
        }),
      );
      setDone(result.message);
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <AuthCard title="Check your inbox" subtitle={done}>
        <Link href="/login" className="text-sm text-accent hover:underline">
          Continue to sign in
        </Link>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Create your account"
      subtitle="Build, test and compare trading strategies — no real money involved."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {form.formMessage && <Alert tone="error">{form.formMessage}</Alert>}
        <Field
          label="Name"
          autoComplete="name"
          required
          maxLength={80}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          error={form.field("display_name")}
        />
        <Field
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={form.field("email")}
        />
        <Field
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          minLength={12}
          hint="At least 12 characters. A passphrase works well."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={form.field("password")}
        />
        <Button type="submit" loading={pending}>
          Create account
        </Button>
      </form>
    </AuthCard>
  );
}
