output "secret_id" {
  description = "ID of the created secret"
  value       = google_secret_manager_secret.main.secret_id
}

output "secret_name" {
  description = "Fully qualified name of the secret (format: projects/{project}/secrets/{secret_id})"
  value       = google_secret_manager_secret.main.name
}
