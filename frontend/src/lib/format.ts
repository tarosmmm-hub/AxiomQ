/** Single source of truth for number/date formatting in the UI. */

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "2-digit",
});

export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

/** Quotas: `null` means unlimited (never render it as 0). */
export function formatQuota(value: number | null | undefined): string {
  if (value === null) return "Unlimited";
  if (value === undefined) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

/**
 * Money formatting per currency. CLP amounts use the Chilean convention (no decimals, "."
 * as thousands separator); USD uses two decimals.
 */
export function formatMoney(value: number, currency: "USD" | "CLP"): string {
  const locale = currency === "CLP" ? "es-CL" : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "CLP" ? 0 : 2,
  }).format(value);
}

/** Safe post-login redirect target: only same-origin relative paths. */
export function safeNextPath(next: string | null | undefined, fallback = "/dashboard"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) {
    return fallback;
  }
  return next;
}
