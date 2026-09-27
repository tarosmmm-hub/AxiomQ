"use client";

import { useQueryClient } from "@tanstack/react-query";
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
import { safeNextPath } from "@/lib/format";

export function LoginForm({ next, notice }: { next?: string; notice?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const form = useFormError();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    form.clear();
    try {
      const user = await unwrap(api.POST("/api/v1/auth/login", { body: { email, password } }));
      queryClient.setQueryData(["me"], user);
      router.replace(safeNextPath(next));
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
      setPending(false);
    }
  }

  return (
    <AuthCard
      title="Sign in"
      subtitle="Welcome back to AxiomQ."
      footer={
        <>
          No account?{" "}
          <Link href="/register" className="text-accent hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {notice && <Alert tone="success">{notice}</Alert>}
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
        <Field
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={form.field("password")}
        />
        <div className="flex items-center justify-between">
          <Link href="/forgot-password" className="text-xs text-muted hover:text-fg">
            Forgot password?
          </Link>
          <Button type="submit" loading={pending}>
            Sign in
          </Button>
        </div>
      </form>
    </AuthCard>
  );
}
