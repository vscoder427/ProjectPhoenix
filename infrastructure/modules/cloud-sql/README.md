# Cloud SQL PostgreSQL Module

Provisions a HIPAA-compliant Cloud SQL PostgreSQL instance with security best practices.

## Features

- **Private IP only** - No public internet access
- **SSL/TLS enforcement** - All connections encrypted
- **Automated backups** - Configurable retention and PITR
- **Secret Manager integration** - Credentials stored securely
- **PHI labeling** - Track databases containing protected health information

## Usage

```hcl
module "employa_core" {
  source = "../modules/cloud-sql"

  project_id    = "employa-prod"
  instance_name = "employa-core"
  database_name = "core"
  db_user       = "core_service"
  network       = "projects/employa-prod/global/networks/employa-vpc"

  # PHI databases need extra retention
  contains_phi           = false
  backup_retention_count = 7

  labels = {
    team = "platform"
  }
}
```

## PHI Database Example

```hcl
module "employa_dave" {
  source = "../modules/cloud-sql"

  project_id    = "employa-prod"
  instance_name = "employa-dave"
  database_name = "dave"
  db_user       = "dave_service"
  network       = "projects/employa-prod/global/networks/employa-vpc"

  # PHI database - extended retention
  contains_phi                   = true
  backup_retention_count         = 30
  transaction_log_retention_days = 7

  labels = {
    team = "ai"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_id | GCP project ID | string | - | yes |
| instance_name | Cloud SQL instance name | string | - | yes |
| database_name | Database to create | string | - | yes |
| db_user | Service user name | string | - | yes |
| network | VPC network self-link | string | - | yes |
| environment | Environment suffix | string | "" | no |
| database_version | PostgreSQL version | string | "POSTGRES_15" | no |
| tier | Machine tier | string | "db-f1-micro" | no |
| contains_phi | PHI data flag | bool | false | no |
| deletion_protection | Prevent deletion | bool | true | no |

## Outputs

| Name | Description |
|------|-------------|
| instance_name | Cloud SQL instance name |
| connection_name | Cloud SQL Proxy connection string |
| private_ip | Private IP address |
| database_name | Database name |
| db_user | Service user name |
| password_secret_id | Secret Manager ID for password |
| dsn_secret_id | Secret Manager ID for DSN |

## Security

This module enforces:
- Private IP only (no public access)
- SSL/TLS required for all connections
- Credentials in Secret Manager (never in Terraform state)
- Automated backups enabled by default

## Connection from Cloud Run

Services connect via Unix socket using the DSN stored in Secret Manager:

```
postgresql://user:pass@/database?host=/cloudsql/project:region:instance
```

See [cloud-sql-patterns.md](../../docs/standards/cloud-sql-patterns.md) for connection patterns.
