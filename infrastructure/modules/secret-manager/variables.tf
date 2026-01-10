variable "project_id" {
  description = "GCP project ID where the secret will be created"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "secret_id" {
  description = "Secret ID (e.g., 'supabase-url', 'gemini-api-key'). Must be unique within the project."
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.secret_id))
    error_message = "Secret ID must contain only letters, numbers, hyphens, and underscores."
  }
}

variable "accessor_service_accounts" {
  description = "List of service account emails that can access this secret (e.g., ['dave-service@project.iam.gserviceaccount.com'])"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Additional labels to apply to the secret"
  type        = map(string)
  default     = {}
}
