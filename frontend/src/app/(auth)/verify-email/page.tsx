import type { Metadata } from "next";

import { VerifyEmail } from "./verify-email";

export const metadata: Metadata = { title: "Verify email" };

export default async function VerifyEmailPage({ searchParams }: PageProps<"/verify-email">) {
  const { token } = await searchParams;
  return <VerifyEmail token={typeof token === "string" ? token : undefined} />;
}
