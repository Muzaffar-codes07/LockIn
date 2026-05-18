import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
const env = process.env.NEXT_PUBLIC_ENV ?? "local";
const release = process.env.NEXT_PUBLIC_GIT_SHA ?? "dev";

if (dsn) {
  Sentry.init({
    dsn,
    release,
    environment: env,
    tracesSampleRate: env === "production" ? 0.1 : 1.0,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
  });
}
