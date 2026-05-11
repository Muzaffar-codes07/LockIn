output "secret_names" {
  value = { for k, s in google_secret_manager_secret.this : k => s.name }
}

output "service_account_emails" {
  value = { for k, sa in google_service_account.app : k => sa.email }
}
