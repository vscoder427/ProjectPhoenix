variable "project_id" {
  description = "GCP project ID where the state bucket will be created"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "bucket_name" {
  description = "Name of the GCS bucket for Terraform state (must be globally unique)"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be 3-63 characters, lowercase letters, numbers, and hyphens."
  }
}

variable "region" {
  description = "GCP region for the state bucket"
  type        = string
  default     = "us-central1"
}

variable "keep_versions" {
  description = "Number of state file versions to keep (older versions are deleted)"
  type        = number
  default     = 5
  validation {
    condition     = var.keep_versions >= 1 && var.keep_versions <= 10
    error_message = "keep_versions must be between 1 and 10."
  }
}

variable "lifecycle_days" {
  description = "Delete non-current versions after this many days"
  type        = number
  default     = 30
  validation {
    condition     = var.lifecycle_days >= 1 && var.lifecycle_days <= 365
    error_message = "lifecycle_days must be between 1 and 365."
  }
}

variable "force_destroy" {
  description = "Allow bucket deletion even if it contains objects (use with caution in production)"
  type        = bool
  default     = false
}

variable "labels" {
  description = "Additional labels to apply to the bucket"
  type        = map(string)
  default     = {}
}
