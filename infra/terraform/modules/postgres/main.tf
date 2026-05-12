resource "google_sql_database_instance" "this" {
  name                = var.name
  project             = var.project_id
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_size         = var.disk_size_gb
    disk_autoresize   = true
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.network_self_link
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true

      backup_retention_settings {
        retained_backups = var.backup_retention_count
      }
    }

    database_flags {
      name  = "cloudsql.enable_pg_cron"
      value = "on"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
      record_client_address   = false
    }
  }
}

resource "google_sql_database" "app" {
  name     = "lockin"
  project  = var.project_id
  instance = google_sql_database_instance.this.name
}

resource "random_password" "app_user" {
  length  = 32
  special = true
}

resource "google_sql_user" "app" {
  name     = "lockin_app"
  project  = var.project_id
  instance = google_sql_database_instance.this.name
  password = random_password.app_user.result
}
