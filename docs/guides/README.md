# Guides Index

Practical, step-by-step guides for working in ProjectPhoenix. These guides complement the [Standards Library](../standards/README.md) by showing you **how to** apply the standards in practice.

## Development Guides

### 🚀 Getting Started

- **[Service Development Workflow](service-development-workflow.md)** - Complete workflow for fixing bugs, adding features, and refactoring service code. Includes minimal, moderate, and full standards levels with examples.
- **[Developer Quick Reference](dev-quick-reference.md)** - Copy-pasteable checklist for day-to-day development work. Use this while implementing changes or in PR descriptions.

### 🏗️ Infrastructure & Operations

- **[IaC GitHub Tracking](iac-github-tracking.md)** - Workflow for Infrastructure as Code (Terraform) changes, milestones, and project tracking.
- **[Setup Terraform Backend](setup-terraform-backend.md)** - Configure Terraform remote state backend for team collaboration.
- **[Setup Versioning](setup-versioning.md)** - Configure semantic versioning with python-semantic-release for automated version management.

## When to Use Which Guide

| **You Want To...** | **Use This Guide** |
|-------------------|-------------------|
| Fix a bug in Dave, AAMeetings, or other services | [Service Development Workflow](service-development-workflow.md) |
| Add a new feature or endpoint | [Service Development Workflow](service-development-workflow.md) |
| Refactor service code | [Service Development Workflow](service-development-workflow.md) |
| Quick checklist while coding | [Developer Quick Reference](dev-quick-reference.md) |
| Create or modify Terraform infrastructure | [IaC GitHub Tracking](iac-github-tracking.md) |
| Set up Terraform for the first time | [Setup Terraform Backend](setup-terraform-backend.md) |
| Configure semantic versioning | [Setup Versioning](setup-versioning.md) |

## Quick Links

### For New Developers

1. Read [Service Development Workflow](service-development-workflow.md) to understand the development process
2. Bookmark [Developer Quick Reference](dev-quick-reference.md) for daily use
3. Check [Standards Library](../standards/README.md) for detailed rules and patterns
4. Review [Golden Service](../../services/golden-service-python/) for canonical implementation examples

### For DevOps/Platform Engineers

1. Read [IaC GitHub Tracking](iac-github-tracking.md) for infrastructure workflow
2. Follow [Setup Terraform Backend](setup-terraform-backend.md) for team setup
3. Check [IaC Standards](../standards/iac-terraform.md) for Terraform conventions

## Standards vs Guides

**Standards** (in `docs/standards/`) define **what** and **why**:
- Rules and requirements
- Best practices and patterns
- Quality gates and compliance
- Architecture decisions

**Guides** (in `docs/guides/`) show **how** and **when**:
- Step-by-step workflows
- Practical examples
- Tool commands
- Troubleshooting tips

## Related Documentation

- **[Standards Library](../standards/README.md)** - 60+ standards documents organized by discipline
- **[Templates](../templates/README.md)** - Reusable templates for ADRs, service scaffolding, decision records
- **[Enterprise Architecture Principles](../enterprise-architecture-principles.md)** - High-level principles guiding all standards
- **[CLAUDE.md](../../CLAUDE.md)** - ProjectPhoenix overview and Claude Code instructions

## Contributing to Guides

Found an issue or want to improve a guide?

1. Create an issue using the [Service Issue template](../../.github/ISSUE_TEMPLATE/service-issue.md)
2. Use label: `documentation`
3. Reference the guide that needs updating

New guide proposals should include:
- **Target audience:** Who will use this guide?
- **Problem solved:** What question does it answer?
- **Gaps filled:** What's missing from existing docs?

## Feedback

These guides are living documents. If you find:
- Steps that don't work
- Missing information
- Confusing explanations
- Outdated commands

Please open an issue or submit a PR to improve them!
