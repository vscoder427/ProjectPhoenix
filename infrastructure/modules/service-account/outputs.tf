output "email" {
  description = "Email address of the service account (format: {account_id}@{project_id}.iam.gserviceaccount.com)"
  value       = google_service_account.main.email
}

output "name" {
  description = "Fully qualified name of the service account (format: projects/{project}/serviceAccounts/{email})"
  value       = google_service_account.main.name
}

output "account_id" {
  description = "Service account ID (same as input)"
  value       = google_service_account.main.account_id
}

output "unique_id" {
  description = "Unique numeric ID of the service account"
  value       = google_service_account.main.unique_id
}

output "member" {
  description = "IAM member string for use in IAM bindings (format: serviceAccount:{email})"
  value       = "serviceAccount:${google_service_account.main.email}"
}
