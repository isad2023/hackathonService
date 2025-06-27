#!/bin/bash

# Push script for hackathon service Docker image

set -e  # Exit on any error

echo "🚀 Starting push process..."

# Load environment variables
if [ -f ".env" ]; then
    source .env
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ .env file not found"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if image exists locally
IMAGE_NAME="${IMAGE_BACKEND:-auxxxxx/prog2025-hackathon_service}"
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo "❌ Image $IMAGE_NAME not found locally. Run build.sh first."
    exit 1
fi

# Login to Docker Hub (you may need to provide credentials)
echo "🔐 Logging in to Docker Hub..."
if ! docker login; then
    echo "❌ Failed to login to Docker Hub"
    exit 1
fi

# Tag the image (in case it needs a specific tag)
echo "🏷️ Tagging image..."
docker tag "$IMAGE_NAME" "$IMAGE_NAME:latest"

# Push the image
echo "📤 Pushing $IMAGE_NAME to registry..."
docker push "$IMAGE_NAME:latest"

# Optional: Push with additional tags
echo "📤 Pushing additional tags..."
# You can add more specific tags here, for example:
# docker tag "$IMAGE_NAME" "$IMAGE_NAME:v1.0"
# docker push "$IMAGE_NAME:v1.0"

# Tag with build timestamp
BUILD_TAG="$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)"
docker tag "$IMAGE_NAME" "$BUILD_TAG"
docker push "$BUILD_TAG"

echo "✅ Push completed successfully!"
echo "🌐 Image pushed to registry: $IMAGE_NAME"
echo "🏷️ Available tags:"
echo "   - $IMAGE_NAME:latest"
echo "   - $BUILD_TAG"
echo ""
echo "ℹ️ To pull this image on another machine:"
echo "   docker pull $IMAGE_NAME:latest" 