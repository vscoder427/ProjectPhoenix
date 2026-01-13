# Cloud SQL PostgreSQL Instance Module
# Provisions a HIPAA-compliant Cloud SQL PostgreSQL instance with:
# - Private IP only (no public access)
# - SSL/TLS enforcement
# - Automated backups
# - Secret Manager integration for credentials

locals {
  # Instance name includes environment for multi-env support
  instance_name = var.environment != "" ? "${var.instance_name}-${var.environment}" : var.instance_name

  # Merge default labels with custom labels
  labels = merge(
    {
      service     = var.instance_name
      environment = var.environment
      managed_by  = "terraform"
      phi         = var.contains_phi ? "true" : "false"
    },
    var.labels
  )
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = local.instance_name
  database_version = var.database_version
  region           = var.region
  project          = var.project_id

  # Prevent accidental deletion
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_size         = var.disk_size
    disk_type         = var.disk_type
    disk_autoresize   = var.disk_autoresize

    # Private IP only - no public access
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network
      require_ssl     = true  # SSL/TLS enforcement (HIPAA requirement)
    }

    # Automated backups (HIPAA requirement)
    backup_configuration {
      enabled                        = var.backup_enabled
      start_time                     = var.backup_start_time
      location                       = var.backup_location
      point_in_time_recovery_enabled = var.point_in_time_recovery
      transaction_log_retention_days = var.transaction_log_retention_days

      backup_retention_settings {
        retained_backups = var.backup_retention_count
        retention_unit   = "COUNT"
      }
    }

    # Maintenance window
    maintenance_window {
      day          = var.maintenance_day
      hour         = var.maintenance_hour
      update_track = var.maintenance_update_track
    }

    # Database flags
    dynamic "database_flags" {
      for_each = var.database_flags
      content {
        name  = database_flags.value.name
        value = database_flags.value.value
      }
    }

    user_labels = local.labels
  }

  lifecycle {
    # Prevent destruction if deletion_protection is enabled
    prevent_destroy = false
  }
}

# Database
resource "google_sql_database" "main" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Generate secure password
resource "random_password" "db_password" {
  length  = 32
  special = false  # Avoid special chars for connection string compatibility
}

# Database user
resource "google_sql_user" "service" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = random_password.db_password.result
}

# Store password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.instance_name}-db-password"
  project   = var.project_id

  labels = local.labels

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Store DSN in Secret Manager
resource "google_secret_manager_secret" "db_dsn" {
  secret_id = "${var.instance_name}-db-dsn"
  project   = var.project_id

  labels = local.labels

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_dsn" {
  secret = google_secret_manager_secret.db_dsn.id
  secret_data = format(
    "postgresql://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.service.name,
    random_password.db_password.result,
    google_sql_database.main.name,
    google_sql_database_instance.main.connection_name
  )
}
