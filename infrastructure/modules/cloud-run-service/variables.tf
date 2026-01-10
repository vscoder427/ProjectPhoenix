variable "project_id" {
  description = "GCP project ID where the Cloud Run service will be deployed"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "service_name" {
  description = "Base name of the Cloud Run service (environment suffix will be added automatically)"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,48}$", var.service_name))
    error_message = "Service name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (production, staging, dev)"
  type        = string
  validation {
    condition     = contains(["production", "staging", "dev"], var.environment)
    error_message = "Environment must be one of: production, staging, dev."
  }
}

variable "image" {
  description = "Container image URL (e.g., 'gcr.io/project-id/service-name:tag')"
  type        = string
}

variable "service_account_email" {
  description = "Email of the service account to run the service as"
  type        = string
}

variable "service_tier" {
  description = "Service tier from service-tiering.md (tier-0, tier-1, tier-2)"
  type        = string
  validation {
    condition     = contains(["tier-0", "tier-1", "tier-2"], var.service_tier)
    error_message = "Service tier must be one of: tier-0, tier-1, tier-2."
  }
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "memory" {
  description = "Memory allocation (e.g., '512Mi', '1Gi', '2Gi')"
  type        = string
  default     = "512Mi"
  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.memory))
    error_message = "Memory must be specified in Mi or Gi (e.g., '512Mi', '2Gi')."
  }
}

variable "cpu" {
  description = "CPU allocation (must be '1', '2', '4', or '8')"
  type        = string
  default     = "1"
  validation {
    condition     = contains(["1", "2", "4", "8"], var.cpu)
    error_message = "CPU must be one of: 1, 2, 4, 8."
  }
}

variable "min_instances" {
  description = "Minimum number of instances (0 = scale to zero)"
  type        = number
  default     = 0
  validation {
    condition     = var.min_instances >= 0 && var.min_instances <= 100
    error_message = "min_instances must be between 0 and 100."
  }
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
  validation {
    condition     = var.max_instances >= 1 && var.max_instances <= 1000
    error_message = "max_instances must be between 1 and 1000."
  }
}

variable "concurrency" {
  description = "Maximum number of concurrent requests per instance"
  type        = number
  default     = 80
  validation {
    condition     = var.concurrency >= 1 && var.concurrency <= 1000
    error_message = "concurrency must be between 1 and 1000."
  }
}

variable "timeout_seconds" {
  description = "Request timeout in seconds (max 3600)"
  type        = number
  default     = 300
  validation {
    condition     = var.timeout_seconds >= 1 && var.timeout_seconds <= 3600
    error_message = "timeout_seconds must be between 1 and 3600."
  }
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8080
  validation {
    condition     = var.container_port >= 1 && var.container_port <= 65535
    error_message = "container_port must be between 1 and 65535."
  }
}

variable "ingress" {
  description = "Ingress settings: 'all', 'internal', or 'internal-and-cloud-load-balancing'"
  type        = string
  default     = "all"
  validation {
    condition     = contains(["all", "internal", "internal-and-cloud-load-balancing"], var.ingress)
    error_message = "ingress must be one of: all, internal, internal-and-cloud-load-balancing."
  }
}

variable "allow_unauthenticated" {
  description = "Allow public unauthenticated access (use with caution)"
  type        = bool
  default     = false
}

variable "vpc_connector" {
  description = "VPC connector for private network access (leave empty for public internet only)"
  type        = string
  default     = ""
}

variable "environment_variables" {
  description = "Environment variables as key-value pairs"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets from Secret Manager as environment variables. Map key is env var name, value is object with {name, version}"
  type = map(object({
    name    = string
    version = string
  }))
  default = {}
}

variable "labels" {
  description = "Additional labels to apply (merged with default labels)"
  type        = map(string)
  default     = {}
}
