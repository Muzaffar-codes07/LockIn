variable "project_id" {
  type = string
}

variable "zone_name" {
  type        = string
  description = "Cloud DNS managed zone resource name."
}

variable "dns_name" {
  type        = string
  description = "FQDN with trailing dot (e.g., \"staging.lockin.app.\")."
}

variable "env" {
  type = string
}
