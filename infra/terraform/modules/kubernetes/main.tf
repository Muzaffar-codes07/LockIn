resource "google_container_cluster" "this" {
  name     = var.name
  project  = var.project_id
  location = var.region

  enable_autopilot = true
  network          = var.network_self_link
  subnetwork       = var.subnet_self_link

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
  }

  deletion_protection = var.deletion_protection
}
