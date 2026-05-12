variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "name" {
  type        = string
  description = "Logical name prefix for network resources (e.g., \"lockin-staging\")."
}

variable "region" {
  type        = string
  description = "Primary region for the subnet and Cloud NAT."
}

variable "primary_cidr" {
  type        = string
  default     = "10.10.0.0/20"
  description = "CIDR for the primary subnet (nodes)."
}

variable "pods_cidr" {
  type        = string
  default     = "10.20.0.0/14"
  description = "Secondary CIDR for GKE pods."
}

variable "services_cidr" {
  type        = string
  default     = "10.24.0.0/20"
  description = "Secondary CIDR for GKE services."
}
