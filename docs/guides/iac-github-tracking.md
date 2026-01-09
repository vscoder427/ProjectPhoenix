# Infrastructure as Code - GitHub Tracking Setup

This guide explains how to set up and use GitHub tracking for the IaC (Terraform) implementation across ProjectPhoenix services.

## Overview

The IaC implementation uses a combination of:
- **GitHub Milestones** (4 phases with due dates)
- **GitHub Issues** (~30 tasks with acceptance criteria)
- **GitHub Project Board** (Kanban view of progress)
- **Pull Requests** (one per phase for code review)

This provides visibility into progress, clear ownership, and automated tracking.

## Quick Start

### 1. Create Milestones and Issues

Run the automated setup script:

```powershell
cd ProjectPhoenix
.\scripts\setup-iac-tracking.ps1
```

This creates:
- 4 milestones (Phase 1-4 with due dates)
- ~30 issues with labels, acceptance criteria, and dependencies
- All issues linked to appropriate milestones

**Preview Mode (Dry Run):**
```powershell
.\scripts\setup-iac-tracking.ps1 -DryRun
```

### 2. Create GitHub Project Board

1. Go to: https://github.com/vscoder427/ProjectPhoenix/projects/new
2. Choose "Board" template
3. Name: "IaC Implementation"
4. Description: "Infrastructure as Code (Terraform) implementation tracking"

**Columns:**
- 📋 Backlog
- 🎯 Phase 1: Foundation
- 🎯 Phase 2: Dave Service
- 🎯 Phase 3: Golden Service
- 🎯 Phase 4: CI/CD
- ✅ Done

**Views:**
- **Board View** (default): Kanban board for status tracking
- **Table View**: Filterable spreadsheet with all metadata
- **Timeline View**: Gantt chart showing schedule

### 3. Add Issues to Project

From the project board:
1. Click "Add items"
2. Search for label: `iac-implementation`
3. Select all issues
4. Click "Add selected items"

### 4. Configure Automation (Optional)

GitHub Projects can auto-move issues:
- **To "In Progress"**: When issue is assigned or referenced in PR
- **To "Done"**: When issue is closed

Settings → Workflows → Enable built-in automations

## Issue Organization

### Labels

Issues are tagged with multiple labels for filtering:

| Label | Purpose |
|-------|---------|
| `phase-1`, `phase-2`, `phase-3`, `phase-4` | Which phase the issue belongs to |
| `standards`, `module`, `service-config`, `ci-cd` | Type of work |
| `critical`, `high-priority`, `medium-priority` | Urgency level |
| `dave`, `golden-service` | Service-specific work |
| `blocked` | Issue cannot proceed due to dependency |
| `needs-review` | Waiting for review/approval |

**Filter Examples:**
- All Phase 1 issues: `label:phase-1`
- Critical issues: `label:critical`
- Dave-specific work: `label:dave`
- Blocked issues: `label:blocked`

### Issue Template

All issues follow a standard template ([.github/ISSUE_TEMPLATE/iac-task.md](.github/ISSUE_TEMPLATE/iac-task.md)):

```markdown
## Task Details
- Phase
- Priority
- Estimated Effort
- Dependencies

## Description
[What needs to be done]

## Acceptance Criteria
- [ ] Testable criterion 1
- [ ] Testable criterion 2

## Files to Create/Modify
- [ ] path/to/file1.tf
- [ ] path/to/file2.md

## Testing/Validation
- [ ] terraform validate passes
- [ ] Manual testing completed

## Notes
[Additional context]
```

## Workflow

### Recommended Workflow: PR-Based

**Branch Strategy:**
```
main
├── feature/iac-phase-1-foundation
├── feature/iac-phase-2-dave
├── feature/iac-phase-3-golden
└── feature/iac-phase-4-cicd
```

**Steps:**

1. **Create Draft PRs Early**
   ```bash
   git checkout -b feature/iac-phase-1-foundation
   git commit --allow-empty -m "feat(iac): Phase 1 foundation - initial commit"
   git push -u origin feature/iac-phase-1-foundation
   gh pr create --draft --title "[Phase 1] IaC Foundation - Standards & Modules" \
                 --body "Implements Phase 1 of IaC plan. Tracking: #[milestone-number]"
   ```

2. **Link Issues to PRs**
   - In PR description, add: `Closes #[issue-number]` for each issue
   - Issues auto-close when PR merges

3. **Work on Issues**
   - Assign yourself to issue
   - Move to "In Progress" column
   - Create files, write code
   - Commit with conventional commits: `feat(iac): create cloud-run-service module`

4. **Check Off Acceptance Criteria**
   - As you complete each criterion, check it off in the issue
   - Add comments with validation results (e.g., "terraform validate passed")

5. **Complete Phase**
   - When all issues in PR are done, mark PR ready for review
   - Move PR to "Ready for Review"
   - Review and merge

6. **Milestone Closes**
   - All issues closed → Milestone auto-completes
   - Move to next phase

### Alternative Workflow: Issue-Only

If not using PRs:

1. Work directly on `main` (or short-lived feature branches)
2. Close issues as work completes
3. Use issue comments to document progress
4. Milestone closes when all issues done

## Tracking Progress

### Daily Standup View

**Project Board → Board View**
- See what's "In Progress"
- Identify blocked issues
- Plan day's work

### Weekly Checkpoint View

**Project Board → Table View**

Filter by milestone and check:
- % complete (issues closed / total issues)
- Are we on track for due date?
- Any blockers?

**Checkpoint Questions (from plan):**

**End of Day 3 (Phase 1):**
- Are all 4 modules complete?
- Does iac-terraform.md cover all topics?
- Can someone follow setup guide independently?

**End of Day 6 (Phase 2):**
- Did Dave Terraform apply successfully?
- Is service healthy?
- Are secrets accessible?

**End of Day 8 (Phase 3):**
- Is Golden Service Terraform working?
- Is pattern reusable?
- Are template updates complete?

**End of Day 10 (Phase 4):**
- Are all 3 CI/CD workflows functional?
- Does terraform-plan work on PRs?
- Can manual apply deploy successfully?

### Executive Summary View

**GitHub Milestones Page**

Navigate to: https://github.com/vscoder427/ProjectPhoenix/milestones

Shows:
- Overall progress (30 issues, X complete)
- Phase-by-phase progress bars
- Due dates and overdue status

## Managing Dependencies

Issues have dependencies documented in the "Dependencies" section.

**Example:**
```markdown
**Dependencies:** #42, #43, #44
```

**Managing Blocked Issues:**

1. If an issue is blocked by another:
   - Add `blocked` label
   - Add comment: "Blocked by #[issue-number]"
   - Move to "Backlog" column

2. When blocker is resolved:
   - Remove `blocked` label
   - Move back to appropriate phase column

## Communication

### Issue Comments

Use issue comments for:
- Progress updates
- Questions/clarifications
- Validation results (e.g., "terraform validate passed ✅")
- Screenshots of working infrastructure

### PR Reviews

Phase PRs should be reviewed by:
- Platform team (Terraform module quality)
- Security team (IAM permissions, secret management)
- Another engineer (code quality, standards adherence)

### Checkpoint Reviews

At each checkpoint (end of Day 3, 6, 8, 10):
- Create summary comment in milestone
- Tag relevant stakeholders
- Link to key artifacts (plan outputs, service URLs, dashboards)

## Troubleshooting

### Script Fails to Create Issues

**Error:** "GitHub CLI not found"
- **Fix:** Install GitHub CLI: https://cli.github.com/

**Error:** "Not authenticated"
- **Fix:** Run `gh auth login` and follow prompts

**Error:** "Permission denied"
- **Fix:** Ensure you have write access to the repository

### Issues Not Showing in Project

- **Fix:** Manually add issues: Project → Add items → Search `label:iac-implementation`

### Milestones Not Linked to Issues

- **Fix:** Re-run script or manually edit issue and select milestone

## References

- **Plan File:** [C:\Users\damiy\.claude\plans\wiggly-wondering-island.md](file:///C:/Users/damiy/.claude/plans/wiggly-wondering-island.md)
- **Issue Template:** [.github/ISSUE_TEMPLATE/iac-task.md](../../.github/ISSUE_TEMPLATE/iac-task.md)
- **Setup Script:** [scripts/setup-iac-tracking.ps1](../../scripts/setup-iac-tracking.ps1)
- **IaC Standard:** [docs/standards/iac-terraform.md](../standards/iac-terraform.md)
- **Standards Governance:** [docs/standards/standards-governance.md](../standards/standards-governance.md)

## Next Steps

1. ✅ Run setup script: `.\scripts\setup-iac-tracking.ps1`
2. ✅ Create GitHub Project Board
3. ✅ Add all issues to project
4. ✅ Create Phase 1 draft PR
5. → Start working on Phase 1 issues!
