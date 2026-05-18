import * as Sentry from "@sentry/nextjs";

const dsn = process.env.SENTRY_DSN_WEB ?? process.env.NEXT_PUBLIC_SENTRY_DSN;
const env = process.env.ENV ?? process.env.NEXT_PUBLIC_ENV ?? "local";
const release = process.env.GIT_SHA ?? process.env.NEXT_PUBLIC_GIT_SHA ?? "dev";

if (dsn) {
  Sentry.init({
    dsn,
    release,
    environment: env,
    tracesSampleRate: env === "production" ? 0.1 : 1.0,
  });
}
