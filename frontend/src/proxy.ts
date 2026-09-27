import { NextResponse, type NextRequest } from "next/server";

/**
 * 1. Proxies /api/* to the FastAPI backend so the session cookie is first-party (same origin).
 * 2. Redirects anonymous visitors of app pages to /login. This is a UX shortcut only: the backend
 *    authorises every request; a stale cookie is handled client-side on the first 401.
 */
const API_URL = process.env.AXIOMQ_API_URL ?? "http://localhost:8000";
const SESSION_COOKIE = "axq_session";

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  if (pathname.startsWith("/api/")) {
    return NextResponse.rewrite(new URL(`${pathname}${search}`, API_URL));
  }
  if (!request.cookies.has(SESSION_COOKIE)) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*", "/dashboard/:path*", "/settings/:path*"],
};
