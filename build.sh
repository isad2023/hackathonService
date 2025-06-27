#!/bin/bash

# Build script for hackathon service

set -e  # Exit on any error

echo "🚀 Starting build process..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in current directory"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Remove old images (optional, uncomment if needed)
# echo "🗑️ Removing old images..."
# docker-compose down --rmi all

# Build the hackathon_service with the specified tag
echo "🏗️ Building the hackathon_service with tag auxxxxx/prog2025-hackathon_service..."
docker build -t auxxxxx/prog2025-hackathon_service .

# Start services with Docker Compose
echo "🏗️ Starting services with Docker Compose..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 3

# Check if services are running
echo "🔍 Checking service status..."
docker ps

# Run tests inside container (if test service exists)
if docker compose config --services | grep -q "test"; then
    echo "🧪 Running tests..."
    docker compose run --rm test
else
    echo "ℹ️ No test service found in docker-compose.yml"
fi

echo "✅ Build completed successfully!"
echo "🌐 Services are running. Check docker-compose ps for details."
echo "🏃 To view logs: docker-compose logs -f"
echo "🛑 To stop services: docker-compose down" 