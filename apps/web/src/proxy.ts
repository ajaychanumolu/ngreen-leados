import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const token = request.cookies.get("leados_demo_token")?.value;
  const isLogin = request.nextUrl.pathname.startsWith("/login");
  if (!token && !isLogin) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (token && isLogin) {
    return NextResponse.redirect(new URL("/overview", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/login",
    "/overview",
    "/research",
    "/research/:path*",
    "/accounts/:path*",
    "/crm",
    "/imports",
    "/contacts",
    "/calling",
    "/calling/:path*",
    "/calls/:path*",
    "/tasks",
    "/reports",
  ],
};
