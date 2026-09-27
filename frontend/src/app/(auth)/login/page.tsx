import type { Metadata } from "next";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in" };

const NOTICES: Record<string, string> = {
  "password-reset": "Your password has been changed. Sign in with the new password.",
};

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const params = await searchParams;
  const next = typeof params.next === "string" ? params.next : undefined;
  const notice = typeof params.notice === "string" ? NOTICES[params.notice] : undefined;
  return <LoginForm next={next} notice={notice} />;
}
