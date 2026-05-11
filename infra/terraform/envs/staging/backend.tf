# Init pattern (run once per machine, never check actual project_id in here):
#   terraform init -backend-config="bucket=lockin-tfstate-${LOCKIN_GCP_PROJECT}"

terraform {
  backend "gcs" {
    prefix = "envs/staging"
    # bucket supplied at init via -backend-config
  }
}
