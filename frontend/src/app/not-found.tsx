import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-2 p-6 text-center">
      <p className="font-mono text-xs text-subtle">404</p>
      <h1 className="text-lg font-semibold">Page not found</h1>
      <Link href="/dashboard" className="text-sm text-accent hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}
