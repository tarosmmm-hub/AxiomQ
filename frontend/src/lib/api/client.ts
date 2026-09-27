import createClient, { type Middleware } from "openapi-fetch";

import { ApiError } from "./errors";
import type { components, paths } from "./schema";

export type Schemas = components["schemas"];
export type User = Schemas["UserOut"];
export type Entitlements = Schemas["EntitlementsOut"];
export type Workspace = Schemas["WorkspaceOut"];

const CSRF_COOKIE = "axq_csrf";
const CSRF_HEADER = "X-AxiomQ-CSRF";
const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function readCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.split("; ").find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : undefined;
}

async function csrfToken(): Promise<string> {
  const existing = readCookie(CSRF_COOKIE);
  if (existing) return existing;
  const response = await fetch("/api/v1/auth/csrf", { credentials: "same-origin" });
  const body = (await response.json()) as { csrf_token: string };
  return body.csrf_token;
}

/** Double-submit CSRF: echo the (signed) cookie value in a header on every mutation. */
const csrfMiddleware: Middleware = {
  async onRequest({ request }) {
    if (UNSAFE.has(request.method.toUpperCase())) {
      request.headers.set(CSRF_HEADER, await csrfToken());
    }
    return request;
  },
};

/** Same-origin client: requests go to /api/* and are proxied to the backend by src/proxy.ts. */
export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin" });
api.use(csrfMiddleware);

/** Throw an ApiError for non-2xx responses; return the typed data otherwise. */
export async function unwrap<T>(
  call: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await call;
  if (!response.ok) throw new ApiError(response.status, error);
  return data as T;
}
