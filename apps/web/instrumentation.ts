// Next 13+ runs this on cold start. We branch on the runtime to load the
// right Sentry config (server vs. edge). Client config is loaded by Next's
// own injection during withSentryConfig wrapping.

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  } else if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}
