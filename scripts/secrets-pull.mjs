#!/usr/bin/env node
// Pull dev secrets from Google Secret Manager into .env.local.
//
// Prereqs (one-time):
//   gcloud auth application-default login
//   gcloud config set project ${LOCKIN_GCP_PROJECT}
//
// Then:
//   LOCKIN_GCP_PROJECT=lockin-staging-XXXXXX pnpm secrets:pull
//
// The script:
//   - reads the canonical secret list below
//   - calls `gcloud secrets versions access latest --secret=<id>` per secret
//   - writes a 0600 .env.local file (Unix; Windows ACLs are best-effort)
//   - reports which secrets were missing (lets you triage in Secret Manager)

import { execFileSync } from "node:child_process";
import { existsSync, writeFileSync, chmodSync } from "node:fs";

const project = process.env.LOCKIN_GCP_PROJECT;
if (!project) {
  process.stderr.write("LOCKIN_GCP_PROJECT must be set.\n");
  process.exit(1);
}

// The single source of truth for which secrets Secret Manager carries.
// Mirrors `secret_ids = [...]` in infra/terraform/envs/{staging,prod}/main.tf.
const CANONICAL_SECRETS = [
  "DATABASE_URL",
  "REDIS_URL",
  "AUTH_SECRET",
  "GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET",
  "SENTRY_DSN_WEB",
  "SENTRY_DSN_API",
  "SENTRY_DSN_MCP",
  "GRAFANA_CLOUD_OTLP_ENDPOINT",
  "GRAFANA_CLOUD_OTLP_AUTH",
];

function gcloudVersion() {
  try {
    const out = execFileSync("gcloud", ["--version"], { encoding: "utf-8" });
    return out.split("\n")[0]?.trim() ?? "unknown";
  } catch {
    return null;
  }
}

const version = gcloudVersion();
if (!version) {
  process.stderr.write("`gcloud` CLI not found on PATH. Install Google Cloud SDK first.\n");
  process.exit(2);
}
process.stdout.write(`Using ${version}\nProject: ${project}\n\n`);

const lines = [];
const missing = [];

for (const name of CANONICAL_SECRETS) {
  try {
    const value = execFileSync(
      "gcloud",
      [
        "secrets",
        "versions",
        "access",
        "latest",
        `--secret=${name}`,
        `--project=${project}`,
      ],
      { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] },
    ).replace(/\r?\n$/, "");
    lines.push(`${name}=${value}`);
    process.stdout.write(`  ok   ${name}\n`);
  } catch {
    missing.push(name);
    process.stdout.write(`  miss ${name}\n`);
  }
}

if (lines.length === 0) {
  process.stderr.write("\nNo secrets pulled. Aborting before overwriting .env.local.\n");
  process.exit(3);
}

const outPath = ".env.local";
if (existsSync(outPath)) {
  process.stdout.write(`\nOverwriting existing ${outPath}\n`);
}
writeFileSync(outPath, lines.join("\n") + "\n");
try {
  chmodSync(outPath, 0o600);
} catch {
  /* Windows; best-effort */
}

process.stdout.write(`\nWrote ${lines.length} secrets to ${outPath} (mode 0600).\n`);
if (missing.length > 0) {
  process.stdout.write(
    `\nNot pulled (${missing.length}): ${missing.join(", ")}\n` +
      "Create them in Secret Manager or remove from CANONICAL_SECRETS if intentionally unused.\n",
  );
}
