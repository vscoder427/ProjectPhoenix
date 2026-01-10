# Secret Manager secret resource (metadata only, no actual secret value)
resource "google_secret_manager_secret" "main" {
  secret_id = var.secret_id
  project   = var.project_id

  # Replication configuration
  replication {
    auto {
      # Automatic replication across all GCP regions
    }
  }

  # Labels for organization
  labels = merge(
    {
      managed_by = "terraform"
    },
    var.labels
  )
}

# Grant IAM access to service accounts
resource "google_secret_manager_secret_iam_member" "accessors" {
  for_each = toset(var.accessor_service_accounts)

  project   = var.project_id
  secret_id = google_secret_manager_secret.main.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value}"
}
