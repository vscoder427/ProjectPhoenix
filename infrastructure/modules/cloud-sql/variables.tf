variable "project_id" {
  description = "GCP project ID"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "instance_name" {
  description = "Base name of the Cloud SQL instance (environment suffix added automatically if set)"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,78}$", var.instance_name))
    error_message = "Instance name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (production, staging, dev) - leave empty for no suffix"
  type        = string
  default     = ""
  validation {
    condition     = var.environment == "" || contains(["production", "staging", "dev"], var.environment)
    error_message = "Environment must be empty or one of: production, staging, dev."
  }
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.database_name))
    error_message = "Database name must start with lowercase letter and contain only lowercase letters, numbers, and underscores."
  }
}

variable "db_user" {
  description = "Name of the database service user"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.db_user))
    error_message = "Database user must start with lowercase letter and contain only lowercase letters, numbers, and underscores."
  }
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
  validation {
    condition     = can(regex("^POSTGRES_[0-9]+$", var.database_version))
    error_message = "Database version must be in format POSTGRES_XX."
  }
}

variable "region" {
  description = "GCP region for Cloud SQL deployment"
  type        = string
  default     = "us-central1"
}

variable "tier" {
  description = "Cloud SQL machine tier (e.g., db-f1-micro, db-g1-small, db-custom-2-4096)"
  type        = string
  default     = "db-f1-micro"
}

variable "availability_type" {
  description = "Availability type: ZONAL or REGIONAL (for HA)"
  type        = string
  default     = "ZONAL"
  validation {
    condition     = contains(["ZONAL", "REGIONAL"], var.availability_type)
    error_message = "Availability type must be ZONAL or REGIONAL."
  }
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 10
  validation {
    condition     = var.disk_size >= 10 && var.disk_size <= 65536
    error_message = "Disk size must be between 10 and 65536 GB."
  }
}

variable "disk_type" {
  description = "Disk type: PD_SSD or PD_HDD"
  type        = string
  default     = "PD_SSD"
  validation {
    condition     = contains(["PD_SSD", "PD_HDD"], var.disk_type)
    error_message = "Disk type must be PD_SSD or PD_HDD."
  }
}

variable "disk_autoresize" {
  description = "Enable automatic disk resize"
  type        = bool
  default     = true
}

variable "network" {
  description = "VPC network self-link for private IP"
  type        = string
}

variable "contains_phi" {
  description = "Whether this database contains PHI (affects logging and retention)"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Prevent accidental deletion of the instance"
  type        = bool
  default     = true
}

# Backup configuration
variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup start time in UTC (HH:MM format)"
  type        = string
  default     = "03:00"
  validation {
    condition     = can(regex("^[0-2][0-9]:[0-5][0-9]$", var.backup_start_time))
    error_message = "Backup start time must be in HH:MM format."
  }
}

variable "backup_location" {
  description = "Backup storage location (region or multi-region like 'us')"
  type        = string
  default     = "us"
}

variable "backup_retention_count" {
  description = "Number of backups to retain"
  type        = number
  default     = 7
  validation {
    condition     = var.backup_retention_count >= 1 && var.backup_retention_count <= 365
    error_message = "Backup retention count must be between 1 and 365."
  }
}

variable "point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "transaction_log_retention_days" {
  description = "Days to retain transaction logs (1-7)"
  type        = number
  default     = 7
  validation {
    condition     = var.transaction_log_retention_days >= 1 && var.transaction_log_retention_days <= 7
    error_message = "Transaction log retention must be between 1 and 7 days."
  }
}

# Maintenance configuration
variable "maintenance_day" {
  description = "Day of week for maintenance (1=Monday, 7=Sunday)"
  type        = number
  default     = 7
  validation {
    condition     = var.maintenance_day >= 1 && var.maintenance_day <= 7
    error_message = "Maintenance day must be between 1 (Monday) and 7 (Sunday)."
  }
}

variable "maintenance_hour" {
  description = "Hour for maintenance window (0-23 UTC)"
  type        = number
  default     = 4
  validation {
    condition     = var.maintenance_hour >= 0 && var.maintenance_hour <= 23
    error_message = "Maintenance hour must be between 0 and 23."
  }
}

variable "maintenance_update_track" {
  description = "Maintenance update track: stable, canary, or week5"
  type        = string
  default     = "stable"
  validation {
    condition     = contains(["stable", "canary", "week5"], var.maintenance_update_track)
    error_message = "Maintenance update track must be stable, canary, or week5."
  }
}

variable "database_flags" {
  description = "List of database flags to set"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "labels" {
  description = "Additional labels to apply (merged with default labels)"
  type        = map(string)
  default     = {}
}
