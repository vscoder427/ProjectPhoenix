$outputFile = "ANTIGRAVITY_BRIEFING.md"
$projectRoot = Get-Location

# Define the list of high-value context files
# Note: warp-frontend spike removed (Firebase deprecated, moved to GCP-native)
# Reference Warp project at workspace root for frontend config
$filesToPack = @(
    "docs/standards/frontend-visual-spec.md",
    "docs/standards/coding-conventions.md",
    "docs/standards/formatting-linting-typing.md",
    "docs/standards/ai-native-development-standards.md",
    "docs/standards/tech-runtime-versions.md"
)

$header = @"
# PROJECT PHOENIX: ANTIGRAVITY CONTEXT INJECTION
Generated on $(Get-Date)

This document contains the consolidated standards, design tokens, and configuration constraints for Project Phoenix.
Use this as your primary source of truth when building frontend components in isolated environments.

---
"@

$header | Out-File -FilePath $outputFile -Encoding utf8

foreach ($file in $filesToPack) {
    if (Test-Path $file) {
        Write-Host "Packing $file..."
        
        $content = Get-Content -Path $file -Raw
        
        $section = @"

# ==============================================================================
# FILE: $file
# ==============================================================================
```$(if ($file.EndsWith(".json")) { "json" } elseif ($file.EndsWith(".ts")) { "typescript" } else { "markdown" })
$content
```

"@
        $section | Out-File -FilePath $outputFile -Append -Encoding utf8
    } else {
        Write-Warning "File not found: $file"
    }
}

Write-Host "Context packed successfully into $outputFile"
