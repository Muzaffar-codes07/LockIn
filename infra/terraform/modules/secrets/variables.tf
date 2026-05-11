variable "project_id" {
  type = string
}

variable "secret_ids" {
  type        = list(string)
  description = "Logical secret names to create in Secret Manager."
}

variable "app_service_accounts" {
  type        = list(string)
  description = "Service-account account IDs that need read access to every listed secret."
}
