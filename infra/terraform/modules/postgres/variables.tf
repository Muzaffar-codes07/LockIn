variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "network_self_link" {
  type        = string
  description = "VPC self-link for private-IP access."
}

variable "tier" {
  type    = string
  default = "db-custom-2-7680"
}

variable "availability_type" {
  type    = string
  default = "ZONAL"
}

variable "disk_size_gb" {
  type    = number
  default = 50
}

variable "backup_retention_count" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = true
}
