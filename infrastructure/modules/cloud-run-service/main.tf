locals {
  # Compute service name with environment suffix
  service_name_full = "${var.service_name}-${var.environment}"

  # Merge default labels with custom labels
  labels = merge(
    {
      service     = var.service_name
      environment = var.environment
      managed_by  = "terraform"
      tier        = var.service_tier
    },
    var.labels
  )

  # Convert environment variables map to list of {name, value} objects
  env_vars = [for k, v in var.environment_variables : {
    name  = k
    value = v
  }]

  # Convert secrets map to list of {name, value_from} objects
  secret_env_vars = [for k, v in var.secrets : {
    name = k
    value_from = [{
      secret_key_ref = {
        name = v.name
        key  = v.version
      }
    }]
  }]
}

resource "google_cloud_run_service" "main" {
  name     = local.service_name_full
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = var.service_account_email
      container_concurrency = var.concurrency
      timeout_seconds      = var.timeout_seconds

      containers {
        image = var.image

        # Resource limits
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        # Environment variables
        dynamic "env" {
          for_each = local.env_vars
          content {
            name  = env.value.name
            value = env.value.value
          }
        }

        # Secrets as environment variables
        dynamic "env" {
          for_each = local.secret_env_vars
          content {
            name = env.value.name
            dynamic "value_from" {
              for_each = env.value.value_from
              content {
                secret_key_ref {
                  name = value_from.value.secret_key_ref.name
                  key  = value_from.value.secret_key_ref.key
                }
              }
            }
          }
        }

        # Health check port
        ports {
          container_port = var.container_port
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = tostring(var.min_instances)
        "autoscaling.knative.dev/maxScale" = tostring(var.max_instances)
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector
      }

      labels = local.labels
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  metadata {
    labels = local.labels

    annotations = {
      "run.googleapis.com/ingress" = var.ingress
    }
  }

  # Lifecycle to prevent destruction due to traffic block changes
  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"]
    ]
  }
}

# Public access (if enabled)
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  service  = google_cloud_run_service.main.name
  location = google_cloud_run_service.main.location
  project  = google_cloud_run_service.main.project
  role     = "roles/run.invoker"
  member   = "allUsers"
}
