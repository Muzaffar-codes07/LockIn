terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.40, < 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "dns_name" {
  type    = string
  default = "lockin.app."
}

module "vpc" {
  source     = "../../modules/vpc"
  project_id = var.project_id
  name       = "lockin-prod"
  region     = var.region
}

module "postgres" {
  source              = "../../modules/postgres"
  project_id          = var.project_id
  name                = "lockin-prod-pg"
  region              = var.region
  network_self_link   = module.vpc.network_self_link
  tier                = "db-custom-4-15360"
  availability_type   = "REGIONAL"
  deletion_protection = true
}

module "redis" {
  source         = "../../modules/redis"
  project_id     = var.project_id
  name           = "lockin-prod-redis"
  region         = var.region
  network_id     = module.vpc.network_id
  tier           = "STANDARD_HA"
  memory_size_gb = 4
}

module "k8s" {
  source              = "../../modules/kubernetes"
  project_id          = var.project_id
  name                = "lockin-prod"
  region              = var.region
  network_self_link   = module.vpc.network_self_link
  subnet_self_link    = module.vpc.subnet_self_link
  deletion_protection = true
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  secret_ids = [
    "DATABASE_URL",
    "REDIS_URL",
    "NEXTAUTH_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "SENTRY_DSN_WEB",
    "SENTRY_DSN_API",
    "SENTRY_DSN_MCP",
    "GRAFANA_CLOUD_OTLP_ENDPOINT",
    "GRAFANA_CLOUD_OTLP_AUTH",
  ]
  app_service_accounts = ["lockin-api", "lockin-mcp", "lockin-deploy"]
}

module "dns" {
  source     = "../../modules/dns"
  project_id = var.project_id
  zone_name  = "lockin-prod"
  dns_name   = var.dns_name
  env        = "prod"
}

output "name_servers" {
  value = module.dns.name_servers
}

output "postgres_connection" {
  value = module.postgres.connection_name
}

output "gke_endpoint" {
  value     = module.k8s.endpoint
  sensitive = true
}
