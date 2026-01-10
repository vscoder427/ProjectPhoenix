# Service account resource
resource "google_service_account" "main" {
  account_id   = var.account_id
  display_name = var.display_name
  description  = var.description
  project      = var.project_id
}

# Grant IAM roles to the service account at project level
resource "google_project_iam_member" "roles" {
  for_each = toset(var.roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.main.email}"
}

# Workload Identity bindings for external workloads (GitHub Actions, etc.)
resource "google_service_account_iam_member" "workload_identity" {
  for_each = toset(var.workload_identity_bindings)

  service_account_id = google_service_account.main.name
  role               = "roles/iam.workloadIdentityUser"
  member             = each.value
}
