output "instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "connection_name" {
  description = "Connection name for Cloud SQL Proxy (project:region:instance)"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.main.name
}

output "db_user" {
  description = "Name of the database service user"
  value       = google_sql_user.service.name
}

output "password_secret_id" {
  description = "Secret Manager secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "dsn_secret_id" {
  description = "Secret Manager secret ID for database DSN"
  value       = google_secret_manager_secret.db_dsn.secret_id
}

output "password_secret_version" {
  description = "Secret Manager secret version for database password"
  value       = google_secret_manager_secret_version.db_password.id
}

output "dsn_secret_version" {
  description = "Secret Manager secret version for database DSN"
  value       = google_secret_manager_secret_version.db_dsn.id
}

output "self_link" {
  description = "Self-link of the Cloud SQL instance"
  value       = google_sql_database_instance.main.self_link
}
