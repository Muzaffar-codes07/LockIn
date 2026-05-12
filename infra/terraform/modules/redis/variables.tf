variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "network_id" {
  type        = string
  description = "VPC ID for PSA-mode private access."
}

variable "tier" {
  type        = string
  default     = "BASIC"
  description = "BASIC (single-node) for staging, STANDARD_HA for prod."
}

variable "memory_size_gb" {
  type    = number
  default = 1
}

variable "reserved_ip_range" {
  type        = string
  default     = "10.30.0.0/29"
  description = "Private-service-access reserved range for Memorystore."
}
