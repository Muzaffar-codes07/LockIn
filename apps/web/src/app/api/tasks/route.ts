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

async function forward(
  url: string,
  init: RequestInit,
): Promise<NextResponse> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    return NextResponse.json({ error: "service_unavailable" }, { status: 503 });
  }
  if (res.status === 204) {
    return new NextResponse(null, { status: 204 });
  }
  const contentType = res.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await res.json()
    : { error: "upstream_error" };
  return NextResponse.json(payload, { status: res.status });
}

export async function GET(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  return forward(`${API_BASE_URL}/v1/tasks`, {
    headers: { Authorization: auth },
    cache: "no-store",
  });
}

export async function POST(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await req.text();
  return forward(`${API_BASE_URL}/v1/tasks`, {
    method: "POST",
    headers: { Authorization: auth, "Content-Type": "application/json" },
    body,
  });
}

// TODO(week-3-4): when PATCH lands, refactor this BFF to a `[id]/route.ts`
// dynamic segment so the proxy URL matches the backend (DELETE /v1/tasks/{id}).
export async function DELETE(req: NextRequest) {
  const auth = bearer(req);
  if (!auth) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const id = req.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "missing id" }, { status: 400 });
  }
  return forward(`${API_BASE_URL}/v1/tasks/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: { Authorization: auth },
  });
}
