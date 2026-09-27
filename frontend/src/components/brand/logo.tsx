export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 font-semibold tracking-tight text-fg">
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true">
        <rect x="1" y="1" width="22" height="22" rx="5" className="fill-accent" />
        <path
          d="M6 17 L10.5 7 L13 12.5 L15 9.5 L18 17"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="stroke-accent-fg"
        />
      </svg>
      {!compact && (
        <span className="text-[15px]">
          Axiom<span className="text-accent">Q</span>
        </span>
      )}
    </span>
  );
}
