"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { useFormError } from "@/components/auth/use-form-error";
import { VerifyEmailBanner } from "@/components/layout/verify-email-banner";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Panel } from "@/components/ui/panel";
import { api, unwrap, type User } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { queryKeys, useMe } from "@/lib/api/hooks";
import { formatDate } from "@/lib/format";

export function Settings() {
  const me = useMe();
  if (!me.data) return null;
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
      {!me.data.email_verified && <VerifyEmailBanner email={me.data.email} />}
      <ProfileForm user={me.data} />
      <PasswordForm />
    </div>
  );
}

function ProfileForm({ user }: { user: User }) {
  const queryClient = useQueryClient();
  const [displayName, setDisplayName] = useState(user.display_name);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const form = useFormError();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    form.clear();
    try {
      const updated = await unwrap(
        api.PATCH("/api/v1/me", { body: { display_name: displayName } }),
      );
      queryClient.setQueryData(queryKeys.me, updated);
      setDisplayName(updated.display_name);
      setSaved(true);
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
    } finally {
      setPending(false);
    }
  }

  return (
    <Panel title="Profile">
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {saved && <Alert tone="success">Profile updated.</Alert>}
        {form.formMessage && <Alert tone="error">{form.formMessage}</Alert>}
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted">Email</span>
          <div className="flex items-center gap-2 text-sm">
            {user.email}
            <Badge tone={user.email_verified ? "positive" : "warning"}>
              {user.email_verified ? "verified" : "unverified"}
            </Badge>
          </div>
        </div>
        <Field
          label="Display name"
          required
          maxLength={80}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          error={form.field("display_name")}
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-subtle">Member since {formatDate(user.created_at)}</span>
          <Button type="submit" loading={pending}>
            Save profile
          </Button>
        </div>
      </form>
    </Panel>
  );
}

function PasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const form = useFormError();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    form.clear();
    try {
      await unwrap(
        api.POST("/api/v1/me/password", {
          body: { current_password: current, new_password: next },
        }),
      );
      setCurrent("");
      setNext("");
      setSaved(true);
    } catch (error) {
      form.setError(error instanceof ApiError ? error : new Error(String(error)));
    } finally {
      setPending(false);
    }
  }

  return (
    <Panel title="Password">
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {saved && (
          <Alert tone="success">Password changed. Your other sessions were signed out.</Alert>
        )}
        {form.formMessage && <Alert tone="error">{form.formMessage}</Alert>}
        <Field
          label="Current password"
          type="password"
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          error={form.field("current_password")}
        />
        <Field
          label="New password"
          type="password"
          autoComplete="new-password"
          hint="At least 12 characters."
          value={next}
          onChange={(e) => setNext(e.target.value)}
          error={form.field("password") ?? form.field("new_password")}
        />
        <div className="flex justify-end">
          <Button type="submit" loading={pending}>
            Change password
          </Button>
        </div>
      </form>
    </Panel>
  );
}
