#!/bin/bash

# Stop script for hackathon service

set -e  # Exit on any error

echo "🛑 Starting stop process..."

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in current directory"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Show current running containers
echo "📋 Current running containers:"
docker compose ps

# Stop all services
echo "🛑 Stopping all services..."
docker compose down

# Optional: Remove volumes (uncomment if needed)
# echo "🗑️ Removing volumes..."
# docker compose down -v

# Optional: Remove images (uncomment if needed)
# echo "🗑️ Removing images..."
# docker compose down --rmi all

# Show status after stopping
echo "📋 Container status after stopping:"
docker compose ps

# Optional: Clean up dangling images and containers
echo "🧹 Cleaning up dangling images and containers..."
docker system prune -f

echo "✅ Stop completed successfully!"
echo "🏁 All services have been stopped"
echo ""
echo "ℹ️ To start services again:"
echo "   ./build.sh"
echo ""
echo "ℹ️ To view logs of stopped containers:"
echo "   docker compose logs"
echo ""
echo "ℹ️ To completely clean up (remove volumes and images):"
echo "   docker compose down -v --rmi all" 