# LockIn Grafana dashboards + alerts

Source of truth for our Grafana Cloud dashboards and the Slack alert that fires when staging burns. JSON files in [`dashboards/`](dashboards) are committed as a *starting skeleton* — author/refine them in the Grafana UI and re-export back here as part of each PR that changes them.

## Repo state vs Grafana Cloud state

| | Lives in repo | Lives in Grafana Cloud |
|---|---|---|
| Dashboard JSON | ✅ committed | imported once + re-exported on changes |
| Alert rules | documented below | configured in UI (Slack contact point + rule) |
| OTLP endpoint URL | `GRAFANA_CLOUD_OTLP_ENDPOINT` env var | account-specific URL |
| Auth token | `GRAFANA_CLOUD_OTLP_AUTH` (Base64 of `instance_id:token`) | issued by Grafana Cloud → Connections → OTLP |

## Three dashboards

| Dashboard | What it shows |
|---|---|
| [`api-golden-signals.json`](dashboards/api-golden-signals.json) | RED panels for `apps/api` — request rate per route, 5xx rate, p50/p95/p99 latency |
| [`postgres-health.json`](dashboards/postgres-health.json) | Cloud SQL: connections, query latency, deadlocks, replication lag |
| [`mcp-health.json`](dashboards/mcp-health.json) | MCP server: tool-call rate, error rate, latency by tool name |

Each file is a starter — minimal layout, real PromQL/TraceQL queries reference span attributes the OTel SDK already emits (`service.name`, `http.status_code`, `http.route`).

## First-time import

1. **Provision the OTLP endpoint** in Grafana Cloud: *Connections → OTLP → Generate Auth*. Stash `endpoint` and `instance_id:token` in Secret Manager as `GRAFANA_CLOUD_OTLP_ENDPOINT` and `GRAFANA_CLOUD_OTLP_AUTH`.
2. **Import each dashboard**: *Dashboards → New → Import → Upload JSON*. Pick the file from this directory.
3. After import, edit titles/queries as needed in the UI, then **Save → Save as JSON file** and overwrite the file here in the next PR. Don't hand-edit the JSON — it's painful and easy to break.

## Slack alert

Two pieces, both configured in the Grafana UI (no Terraform yet — that's a follow-up):

### 1. Contact point: `#lockin-test-alerts`

*Alerting → Contact points → New*. Type: `Slack`. Webhook URL from a Slack incoming-webhook integration in `#lockin-test-alerts`. Test from the UI.

### 2. Alert rule: `api 5xx > 0`

*Alerting → Alert rules → New*:

```
Folder: lockin
Group: api
Name: api 5xx rate > 0 over 1m

Query A (PromQL on the metrics datasource):
  sum(rate(otelcol_exporter_sent_spans{service_name="lockin-api", status_code="STATUS_CODE_ERROR"}[1m]))

Condition: A > 0
Evaluate: every 30s for 1m

Annotations:
  summary: lockin-api is throwing 5xx in {{ $labels.deployment_environment }}
  runbook_url: https://github.com/Muzaffar-codes07/LockIn/blob/main/docs/runbooks/api-5xx.md

Contact point: #lockin-test-alerts
No data: alerting
```

## Acceptance test (the Week 1-2 handoff requirement)

After this PR merges, in **staging**:

```bash
# from a shell with staging API URL
curl -fsSL https://staging.api.lockin.app/v1/__debug__/force_500 || true
```

Within 60s you should see, in order:

1. **Sentry** issue with the `ForcedFailure` stack trace
2. **Grafana** error-rate panel on `api-golden-signals` rises
3. **Slack** `#lockin-test-alerts` message firing the `api 5xx rate > 0` rule

`force_500` is gated to non-production environments (see [`apps/api/app/api/v1/routes/debug.py`](../../apps/api/app/api/v1/routes/debug.py)).

## What's not in this PR

- Terraform-ifying the contact point + alert rule. Grafana Cloud has Terraform support; not worth the bootstrap cost until we have >1 alert.
- Synthetic uptime check ping. Tracked under `feat/synthetic-uptime` (P2).
- Per-tenant dashboards. P3+.
