output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.main.name
}

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.main.status[0].url
}

output "service_id" {
  description = "Fully qualified service ID"
  value       = google_cloud_run_service.main.id
}

output "service_location" {
  description = "Region where the service is deployed"
  value       = google_cloud_run_service.main.location
}

output "latest_revision_name" {
  description = "Name of the latest ready revision"
  value       = google_cloud_run_service.main.status[0].latest_ready_revision_name
}
