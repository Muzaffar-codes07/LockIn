resource "google_secret_manager_secret" "this" {
  for_each = toset(var.secret_ids)

  project   = var.project_id
  secret_id = each.value

  replication {
    auto {}
  }
}

resource "google_service_account" "app" {
  for_each = toset(var.app_service_accounts)

  project      = var.project_id
  account_id   = each.value
  display_name = "App SA: ${each.value}"
}

locals {
  access_pairs = {
    for pair in flatten([
      for secret in var.secret_ids : [
        for sa in var.app_service_accounts : {
          key    = "${secret}::${sa}"
          secret = secret
          sa     = sa
        }
      ]
    ]) : pair.key => pair
  }
}

resource "google_secret_manager_secret_iam_member" "access" {
  for_each = local.access_pairs

  project   = var.project_id
  secret_id = google_secret_manager_secret.this[each.value.secret].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app[each.value.sa].email}"
}
