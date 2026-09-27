import type { ReactNode } from "react";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-14 items-center justify-between px-4 md:px-8">
        <Logo />
        <ThemeToggle />
      </header>
      <main className="flex flex-1 items-start justify-center px-4 pt-[8vh] pb-12">
        <div className="w-full max-w-sm">{children}</div>
      </main>
      <footer className="px-4 py-4 text-center text-[11px] text-subtle md:px-8">
        Research and simulation only. No real-money trading. Past performance does not guarantee
        future results.
      </footer>
    </div>
  );
}
