# LockIn Terraform — GCP

Two environments (`envs/staging`, `envs/prod`) compose six modules under `modules/`. State lives in a per-project GCS bucket.

## One-time bootstrap (per GCP project)

State storage must exist before `terraform init` can run. Bootstrap from outside Terraform:

```pwsh
gcloud storage buckets create gs://lockin-tfstate-$env:LOCKIN_GCP_PROJECT `
  --project=$env:LOCKIN_GCP_PROJECT `
  --location=us-central1 `
  --uniform-bucket-level-access `
  --public-access-prevention=enforced
gcloud storage buckets update gs://lockin-tfstate-$env:LOCKIN_GCP_PROJECT --versioning
```

POSIX equivalent:

```bash
gcloud storage buckets create "gs://lockin-tfstate-${LOCKIN_GCP_PROJECT}" \
  --project="$LOCKIN_GCP_PROJECT" \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --public-access-prevention=enforced
gcloud storage buckets update "gs://lockin-tfstate-${LOCKIN_GCP_PROJECT}" --versioning
```

## Init + plan + apply

```pwsh
# Staging
cd infra/terraform/envs/staging
cp terraform.tfvars.example terraform.tfvars   # fill in real project_id
terraform init -backend-config="bucket=lockin-tfstate-$env:LOCKIN_GCP_PROJECT"
terraform plan
terraform apply
```

`envs/prod` follows the same pattern with the prod GCS bucket and `envs/prod` state prefix.

## TimescaleDB activation (one-time per Cloud SQL instance)

`postgres` module enables the right flags but the extension itself is enabled at the SQL level:

```pwsh
gcloud sql connect lockin-staging-pg --user=lockin_app --database=lockin
```

Then in the psql prompt:

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

The Alembic migration at `apps/api/alembic/versions/0001_timescale_events_hypertable.py` (Week 1–2 Task 14, deferred) assumes the extension is already present.

## GitHub Actions OIDC → GCP

CI workflows in `.github/workflows/` authenticate to GCP via Workload Identity Federation. The pool + provider are **not** part of this Terraform; they must be set up manually once per project:

```bash
gcloud iam workload-identity-pools create github \
  --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github \
  --location=global --workload-identity-pool=github \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

Then bind a service account (`lockin-deploy`) to it. Document the resulting provider URN in the repo's GitHub Secrets as `GCP_WORKLOAD_IDENTITY_PROVIDER`. Bootstrapping this in Terraform is a chicken-and-egg problem (TF needs to authenticate to create the provider it would use). Future Phase: move into Terraform once authenticated via a long-lived deploy-only SA.

## Cleanup

Order matters — destroy in reverse-dependency order. Terraform handles this within an env, but if you cross envs:

```bash
terraform -chdir=infra/terraform/envs/staging destroy
# After destroy completes, optionally delete the state file in GCS for absolute zero remnants:
gcloud storage rm "gs://lockin-tfstate-${LOCKIN_GCP_PROJECT}/envs/staging/default.tfstate" --recursive
```

## Module map

| Module       | What it provisions                                                    |
| ------------ | --------------------------------------------------------------------- |
| `vpc`        | VPC, primary subnet (with secondary ranges for GKE pods/services), Cloud NAT, PSA reservation for Cloud SQL + Memorystore |
| `postgres`   | Cloud SQL Postgres 16 + IAM auth + pg_cron + backups + insights        |
| `redis`      | Memorystore Redis 7.2 (auth-enabled, TLS, PSA-mode)                    |
| `kubernetes` | GKE Autopilot, private nodes, Workload Identity, REGULAR channel       |
| `secrets`    | Secret Manager entries + app service accounts + IAM bindings           |
| `dns`        | Cloud DNS managed zone with DNSSEC                                     |
