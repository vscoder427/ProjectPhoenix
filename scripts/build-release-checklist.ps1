# Placeholder release checklist builder.
# Extend this script to pull CI artifact URLs and fill release readiness metadata.

param(
    [string]$ServiceName = "unknown",
    [string]$ReleaseTag = "manual",
    [string]$ChecklistPath = ""
)

if (-not $ChecklistPath) {
    $ChecklistPath = "docs/releases/$($ServiceName)/$(Get-Date -Format yyyy-MM-dd)-$ReleaseTag/readiness.md"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ChecklistPath) | Out-Null
$content = @"
# Release Readiness Checklist

- Service: $ServiceName
- Release: $ReleaseTag
- SLO burn-rate summary: TODO
- SBOM: TODO
- Security scans: TODO
- Drift summary: TODO
- Config changes: TODO
- Release notes link: TODO
"@

$content | Out-File -FilePath $ChecklistPath -Encoding UTF8
Write-Output "Generated release checklist at $ChecklistPath"

return $ChecklistPath
