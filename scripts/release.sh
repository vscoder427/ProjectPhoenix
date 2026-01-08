#!/bin/bash
# Interactive release helper for solo developer

set -e

SERVICE=$1
DRY_RUN=${2:-false}

if [ -z "$SERVICE" ]; then
    echo "Usage: ./scripts/release.sh <service> [dry-run]"
    echo ""
    echo "Services: dave, golden-service-python"
    exit 1
fi

echo "🚀 Release Helper for $SERVICE"
echo ""

# Check if on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Not on main branch (current: $BRANCH)"
    echo "   Switch to main to release"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ Uncommitted changes detected"
    echo "   Commit all changes before releasing"
    exit 1
fi

# Get current version
cd "services/$SERVICE"
CURRENT_VERSION=$(python -c "import sys; sys.path.insert(0, 'api'); from app import __version__; print(__version__)")
echo "📦 Current version: $CURRENT_VERSION"

# Analyze commits since last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    echo "📜 Commits since $LAST_TAG:"
    git log $LAST_TAG..HEAD --oneline --no-decorate | head -10
else
    echo "📜 No previous tags found"
fi

echo ""

# Run semantic-release in dry-run mode
echo "🔍 Analyzing version bump..."
cd "$OLDPWD"

if [ "$DRY_RUN" = "dry-run" ]; then
    echo "🧪 DRY RUN MODE"
    cd "services/$SERVICE"
    pip install -q python-semantic-release >/dev/null 2>&1
    semantic-release version --no-commit --no-tag --no-push
    echo ""
    echo "✅ Dry run complete. No changes made."
    exit 0
fi

# Confirm release
echo ""
read -p "Proceed with release? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Release cancelled"
    exit 0
fi

# Trigger release workflow
echo "🚀 Triggering release workflow..."
"C:\Program Files\GitHub CLI\gh.exe" workflow run semantic-release.yml \
    -f service="$SERVICE" \
    -f dry_run="false"

echo "✅ Release workflow triggered"
echo "   Monitor: https://github.com/vscoder427/ProjectPhoenix/actions"
