import { auth } from "@/auth";

export const GET = auth((req) => {
  if (!req.auth) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  return Response.json({
    user_id: req.auth.user_id,
    email: req.auth.user?.email ?? null,
    providers: req.auth.providers,
  });
});
