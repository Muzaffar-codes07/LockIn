resource "google_dns_managed_zone" "this" {
  name        = var.zone_name
  project     = var.project_id
  dns_name    = var.dns_name
  description = "LockIn ${var.env} zone"
  visibility  = "public"

  dnssec_config {
    state = "on"
  }
}
