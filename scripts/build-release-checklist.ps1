# Placeholder release checklist builder.
# Extend this script to pull CI artifact URLs and fill release readiness metadata.

param(
    [string]$ServiceName = "unknown",
    [string]$ReleaseTag = "unknown",
    [string]$ChecklistPath = "docs/releases/$($ServiceName)/$(Get-Date -Format yyyy-MM-dd)-$ReleaseTag/readiness.md"
)

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ChecklistPath) | Out-Null
$content = @"
# Release Readiness Checklist

- Service: $ServiceName
- Release: $ReleaseTag
- SLOs: TODO
- SBOM: TODO
- Security scans: TODO
- Drift summary: TODO
- Config changes: TODO
- Release notes: TODO
"@

$content | Out-File -FilePath $ChecklistPath -Encoding UTF8
Write-Output "Generated release checklist at $ChecklistPath"
