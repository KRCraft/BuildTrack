import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Public routes that don't require auth
const PUBLIC_PATHS = ["/login", "/register", "/_next", "/favicon.ico", "/api"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p)) || pathname === "/";
  
  // Check for access token in sessionStorage is not available in middleware (cookies only)
  // We use refresh cookie presence as hint; actual auth is validated via API
  const hasRefreshCookie = request.cookies.has("buildtrack_refresh");
  const hasAccessCookie = request.cookies.has("buildtrack_access");

  // Attach security headers (also set via next.config, but middleware ensures)
  const response = NextResponse.next();
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");

  // If accessing protected route without any refresh hint, redirect to login
  // Note: sessionStorage token not visible to middleware, so we only guard via refresh cookie
  // This is soft guard - hard guard is in AuthProvider + API 401 handling
  if (!isPublic && !hasRefreshCookie && !hasAccessCookie) {
    // Allow through but let client handle redirect to avoid false positives for SPA token
    // Uncomment to enforce hard redirect:
    // return NextResponse.redirect(new URL("/login", request.url));
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
