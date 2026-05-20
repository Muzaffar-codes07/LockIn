// BFF proxy: the browser calls this same-origin route; it reads the HttpOnly
// NextAuth session-token cookie and forwards it as a Bearer token to the
// FastAPI backend. This keeps the backend URL and the token off the client
// and avoids CORS entirely.

import { type NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

// Must match the cookie name configured in apps/web/src/auth.ts.
const SESSION_COOKIE =
  process.env.NODE_ENV === "production"
    ? "__Secure-lockin.session-token"
    : "lockin.session-token";

function bearer(req: NextRequest): string | null {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  return token ? `Bearer ${token}` : null;
}

export async function GET(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const res = await fetch(`${API_BASE_URL}/v1/tasks`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await req.text();
  const res = await fetch(`${API_BASE_URL}/v1/tasks`, {
    method: "POST",
    headers: { Authorization: auth, "Content-Type": "application/json" },
    body,
  });
  return NextResponse.json(await res.json(), { status: res.status });
}
