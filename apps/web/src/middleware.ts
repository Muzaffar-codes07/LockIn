import { auth } from "@/auth";

export default auth((req) => {
  const isProtected =
    req.nextUrl.pathname.startsWith("/dashboard") ||
    req.nextUrl.pathname.startsWith("/api/me");

  if (isProtected && !req.auth) {
    const url = new URL("/api/auth/signin", req.nextUrl.origin);
    return Response.redirect(url);
  }
});

export const config = {
  matcher: ["/dashboard/:path*", "/api/me/:path*"],
};
