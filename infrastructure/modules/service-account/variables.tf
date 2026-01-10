variable "project_id" {
  description = "GCP project ID where the service account will be created"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "account_id" {
  description = "Service account ID (e.g., 'dave-service-prod'). Must be 6-30 characters, lowercase letters, digits, and hyphens."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.account_id))
    error_message = "Account ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "display_name" {
  description = "Human-readable display name for the service account"
  type        = string
}

variable "description" {
  description = "Description of the service account's purpose"
  type        = string
  default     = ""
}

variable "roles" {
  description = "List of IAM roles to grant to the service account at project level (e.g., ['roles/secretmanager.secretAccessor', 'roles/logging.logWriter'])"
  type        = list(string)
  default     = []
}

variable "workload_identity_bindings" {
  description = "List of Workload Identity Federation principals that can impersonate this service account (e.g., ['principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/attribute.repository/org/repo'])"
  type        = list(string)
  default     = []
}
