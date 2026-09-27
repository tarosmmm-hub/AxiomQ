"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/components/ui/cn";
import { Spinner } from "@/components/ui/spinner";
import { api, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { useMe, useWorkspaces } from "@/lib/api/hooks";

import { ThemeToggle } from "./theme-toggle";

interface NavItem {
  href: string;
  label: string;
  available: boolean;
}

// Modules not built yet are shown disabled rather than as pages with placeholder data.
const NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", available: true },
  { href: "/strategies", label: "Strategies", available: false },
  { href: "/backtests", label: "Backtests", available: false },
  { href: "/compare", label: "Compare", available: false },
  { href: "/paper", label: "Paper trading", available: false },
  { href: "/data", label: "Market data", available: false },
  { href: "/settings", label: "Settings", available: true },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const me = useMe();
  const workspaces = useWorkspaces();
  const [signingOut, setSigningOut] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  const unauthenticated = me.error instanceof ApiError && me.error.status === 401;
  useEffect(() => {
    if (unauthenticated) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [unauthenticated, pathname, router]);

  async function signOut() {
    setSigningOut(true);
    try {
      await unwrap(api.POST("/api/v1/auth/logout"));
    } finally {
      queryClient.clear();
      router.replace("/login");
    }
  }

  if (me.isPending || unauthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted">
        <Spinner />
      </div>
    );
  }
  if (me.isError) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6 text-sm text-negative">
        Could not reach the AxiomQ API. Check that the backend is running and reload.
      </div>
    );
  }

  const workspace = workspaces.data?.[0];
  const nav = (
    <nav aria-label="Main" className="flex flex-col gap-0.5 p-2">
      {NAV.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        if (!item.available) {
          return (
            <span
              key={item.href}
              aria-disabled="true"
              className="flex h-8 cursor-not-allowed items-center justify-between rounded-md px-2.5 text-sm text-subtle"
            >
              {item.label}
              <span className="font-mono text-[9px] tracking-wider uppercase">soon</span>
            </span>
          );
        }
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setNavOpen(false)}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex h-8 items-center rounded-md px-2.5 text-sm transition-colors",
              active ? "bg-raised font-medium text-fg" : "text-muted hover:bg-raised hover:text-fg",
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-line bg-surface md:flex">
        <div className="flex h-12 items-center border-b border-line px-4">
          <Logo />
        </div>
        {nav}
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 items-center justify-between gap-3 border-b border-line bg-surface px-4">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className="rounded-md border border-line px-2 py-1 text-xs text-muted md:hidden"
              aria-expanded={navOpen}
              aria-controls="mobile-nav"
              onClick={() => setNavOpen((open) => !open)}
            >
              Menu
            </button>
            <span className="hidden truncate text-sm text-muted sm:inline">
              {workspace?.name ?? ""}
            </span>
            {workspace && <Badge tone="accent">{workspace.plan}</Badge>}
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <span className="hidden text-sm text-muted sm:inline" data-testid="user-name">
              {me.data.display_name}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="whitespace-nowrap"
              onClick={signOut}
              loading={signingOut}
            >
              Sign out
            </Button>
          </div>
        </header>
        {navOpen && (
          <div id="mobile-nav" className="border-b border-line bg-surface md:hidden">
            {nav}
          </div>
        )}
        <main className="flex-1 p-4 md:p-6">{children}</main>
        <footer className="border-t border-line px-4 py-3 text-[11px] text-subtle md:px-6">
          AxiomQ does not execute real-money trades. Backtests and paper trading are simulations and
          do not guarantee future results.
        </footer>
      </div>
    </div>
  );
}
