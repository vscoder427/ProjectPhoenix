#!/bin/bash
# Install git hooks

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."

# Pre-commit hook
cp "$REPO_ROOT/scripts/git-hooks/pre-commit-version-check" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Hooks installed successfully"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: Version bump preview"
