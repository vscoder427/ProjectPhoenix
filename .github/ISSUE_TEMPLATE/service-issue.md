---
name: Service Bug or Feature
about: Track bug fixes or feature development for ProjectPhoenix microservices
title: '[SERVICE] Brief description'
labels: ''
assignees: ''
---

## Issue Type

- [ ] Bug Fix
- [ ] Feature/Enhancement
- [ ] Refactoring
- [ ] Documentation

## Service

**Affected Service(s):** (e.g., Dave, AAMeetings, CareerIntelligence, UserOnboarding)

## Description

### For Bugs:
**Observed Behavior:**
[What's happening now]

**Expected Behavior:**
[What should happen]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [See error]

### For Features:
**User Story:**
As a [type of user], I want [goal] so that [benefit].

**Proposed Solution:**
[Brief description of how this should work]

## Impact

**Severity:** [Critical / High / Medium / Low]

**User Impact:**
[How does this affect end users or the system?]

**Business Value:** (for features)
[Why is this important? What problem does it solve?]

## Complexity Assessment

**Estimated Complexity:** [Simple / Moderate / Complex]

- **Simple:** < 50 lines, 1 file, obvious fix
- **Moderate:** 2-5 files, new endpoint, architectural impact
- **Complex:** Multiple services, breaking change, new patterns

**Estimated Standards Level:** [Minimal / Moderate / Full]

(See [Service Development Workflow](../../docs/guides/service-development-workflow.md) for details)

## Acceptance Criteria

- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]
- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)

## Technical Details

### For Bugs:
**Error Logs:**
```
[Paste relevant logs, stack traces, or error messages]
```

**Environment:**
- Service version:
- Python version:
- Cloud Run region:
- First observed:

### For Features:
**API Changes:**
[New endpoints, request/response formats]

**Data Model Changes:**
[New database tables, fields, RLS policies]

**External Dependencies:**
[New libraries, external APIs, infrastructure]

## Affected Files (Estimated)

- [ ] `services/{service}/app/api/*.py`
- [ ] `services/{service}/app/models/*.py`
- [ ] `services/{service}/tests/*.py`
- [ ] `docs/services/{service}/spec.md`
- [ ] `docs/services/{service}/runbook.md`

## Testing Requirements

- [ ] Unit tests added/updated
- [ ] Integration tests cover the scenario
- [ ] Manual testing completed
- [ ] Contract testing (if API changed)
- [ ] Performance testing (if user-facing)

## Documentation Requirements

- [ ] Inline code comments (if logic complex)
- [ ] Service spec.md updated (if API/behavior changed)
- [ ] Runbook.md updated (if operational procedures changed)
- [ ] ADR created (if architectural decision)
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if setup/usage changed)

## Dependencies

**Blocked By:** #[issue-number] (if applicable)

**Blocks:** #[issue-number] (if applicable)

**Related To:** #[issue-number] (if applicable)

## Security & Compliance

- [ ] Involves PHI/PII handling
- [ ] Requires security review
- [ ] Impacts HIPAA compliance
- [ ] Changes authentication/authorization
- [ ] Modifies secrets management

**If any checked, ensure:**
- Security review checklist completed
- Threat model reviewed
- ADR created for security decisions

## Notes

[Any additional context, references, or considerations]

**References:**
- Related documentation:
- Similar issues:
- External resources:
