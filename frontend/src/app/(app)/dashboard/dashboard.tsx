"use client";

import { VerifyEmailBanner } from "@/components/layout/verify-email-banner";
import { Badge } from "@/components/ui/badge";
import { EmptyState, Panel } from "@/components/ui/panel";
import { Spinner } from "@/components/ui/spinner";
import { useEntitlements, useMe } from "@/lib/api/hooks";
import { formatQuota } from "@/lib/format";

// Market coverage planned for the MVP (ARCHITECTURE.md §6.1). This is configuration, not data:
// no prices are shown until a dataset with documented provenance is imported.
const MARKETS = [
  { name: "United States", detail: "NYSE · NASDAQ · ARCA", calendar: "XNYS", currency: "USD" },
  { name: "Chile", detail: "Bolsa de Santiago · IPSA universe", calendar: "XSGO", currency: "CLP" },
];

export function Dashboard() {
  const me = useMe();
  const entitlements = useEntitlements();

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted">
            {me.data ? `Welcome, ${me.data.display_name}.` : ""} Your research workspace.
          </p>
        </div>
        <div className="flex gap-1.5">
          <Badge tone="neutral">Backtest</Badge>
          <Badge tone="neutral">Paper</Badge>
          <Badge tone="neutral">Live · disabled</Badge>
        </div>
      </div>

      {me.data && !me.data.email_verified && <VerifyEmailBanner email={me.data.email} />}

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Strategies" className="lg:col-span-2">
          <EmptyState
            title="No strategies yet"
            description="The strategy builder is not available yet. Strategies you create will appear here with their versions."
          />
        </Panel>

        <Panel
          title="Plan & limits"
          actions={entitlements.data && <Badge tone="accent">{entitlements.data.plan.code}</Badge>}
        >
          {entitlements.isPending ? (
            <Spinner className="text-muted" />
          ) : entitlements.data ? (
            <dl className="tabular grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted">Backtests per day</dt>
              <dd className="text-right font-mono">
                {formatQuota(entitlements.data.quotas.backtests_per_day)}
              </dd>
              <dt className="text-muted">Paper accounts</dt>
              <dd className="text-right font-mono">
                {formatQuota(entitlements.data.quotas.paper_accounts)}
              </dd>
              <dt className="text-muted">Workspace members</dt>
              <dd className="text-right font-mono">
                {formatQuota(entitlements.data.quotas.max_workspace_members)}
              </dd>
              <dt className="text-muted">Shared strategies</dt>
              <dd className="text-right font-mono">
                {entitlements.data.features.shared_strategies ? "Yes" : "No"}
              </dd>
            </dl>
          ) : (
            <p className="text-sm text-negative">Could not load plan limits.</p>
          )}
        </Panel>

        <Panel title="Recent backtests" className="lg:col-span-2">
          <EmptyState
            title="No backtests yet"
            description="Backtest results will be computed by the AxiomQ engine from real historical datasets. Nothing is shown until a backtest has actually run."
          />
        </Panel>

        <Panel title="Markets">
          <ul className="flex flex-col divide-y divide-line">
            {MARKETS.map((market) => (
              <li
                key={market.calendar}
                className="flex items-center justify-between py-2 first:pt-0"
              >
                <div>
                  <p className="text-sm font-medium">{market.name}</p>
                  <p className="text-xs text-muted">{market.detail}</p>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge>{market.calendar}</Badge>
                  <Badge>{market.currency}</Badge>
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-subtle">No datasets imported yet.</p>
        </Panel>

        <Panel title="Paper trading" className="lg:col-span-2">
          <EmptyState
            title="No paper accounts"
            description="Paper trading runs strategies on new market data with virtual cash, fully separated from backtests."
          />
        </Panel>

        <Panel title="Recent experiments">
          <EmptyState
            title="No experiments"
            description="Every backtest is stored as a reproducible experiment."
          />
        </Panel>
      </div>
    </div>
  );
}
