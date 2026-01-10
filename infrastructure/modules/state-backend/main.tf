# Google Cloud Storage bucket for Terraform state
resource "google_storage_bucket" "terraform_state" {
  name     = var.bucket_name
  location = var.region
  project  = var.project_id

  # Force destroy allows bucket deletion even if it contains objects
  # Set to false in production to prevent accidental deletion
  force_destroy = var.force_destroy

  # Uniform bucket-level access (recommended for security)
  uniform_bucket_level_access = true

  # Versioning configuration
  versioning {
    enabled = true
  }

  # Lifecycle rule to manage old versions
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = var.keep_versions
      days_since_noncurrent_time = var.lifecycle_days
    }
  }

  # Labels for organization and cost tracking
  labels = merge(
    {
      purpose    = "terraform-state"
      managed_by = "terraform"
    },
    var.labels
  )
}
