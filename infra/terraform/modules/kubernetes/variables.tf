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
  type = string
}

variable "subnet_self_link" {
  type = string
}

variable "master_cidr" {
  type        = string
  default     = "172.16.0.0/28"
  description = "CIDR for the GKE control-plane (must not overlap pod/service CIDRs)."
}

variable "deletion_protection" {
  type    = bool
  default = true
}
