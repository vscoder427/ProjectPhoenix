output "bucket_name" {
  description = "Name of the created GCS bucket"
  value       = google_storage_bucket.terraform_state.name
}

output "bucket_url" {
  description = "GCS URL of the bucket (format: gs://bucket-name)"
  value       = google_storage_bucket.terraform_state.url
}

output "bucket_self_link" {
  description = "Self-link (URI) of the bucket"
  value       = google_storage_bucket.terraform_state.self_link
}
