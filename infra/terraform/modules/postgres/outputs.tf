output "instance_name" {
  value = google_sql_database_instance.this.name
}

output "connection_name" {
  value = google_sql_database_instance.this.connection_name
}

output "private_ip" {
  value = google_sql_database_instance.this.private_ip_address
}

output "app_user_password" {
  value     = random_password.app_user.result
  sensitive = true
}

output "database_name" {
  value = google_sql_database.app.name
}
