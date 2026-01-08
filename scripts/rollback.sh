#!/bin/bash
# Rollback to previous version

SERVICE=$1
TARGET_VERSION=$2

if [ -z "$SERVICE" ] || [ -z "$TARGET_VERSION" ]; then
    echo "Usage: ./scripts/rollback.sh <service> <version>"
    echo ""
    echo "Example: ./scripts/rollback.sh dave 1.2.3"
    exit 1
fi

echo "🔄 Rollback $SERVICE to $TARGET_VERSION"
echo ""

# Check if version exists
TAG="v$TARGET_VERSION"
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "❌ Tag $TAG not found"
    exit 1
fi

# Show what will be deployed
echo "📦 Target version info:"
git show "$TAG:services/$SERVICE/api/app/__version__.py" | grep __version__

echo ""
read -p "Deploy this version to Cloud Run? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelled"
    exit 0
fi

# Deploy previous version
echo "🚀 Deploying $SERVICE:$TARGET_VERSION to Cloud Run..."

# Note: Replace with actual gcloud command for your project
echo "⚠️  Manual step required:"
echo "   gcloud run deploy ${SERVICE}-service \\"
echo "     --image=gcr.io/\$(gcloud config get-value project)/${SERVICE}-service:$TARGET_VERSION \\"
echo "     --region=us-central1 \\"
echo "     --platform=managed"

echo ""
echo "Run the command above to complete the rollback."
