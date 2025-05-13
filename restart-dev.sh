#!/bin/zsh

echo "🔄 Stopping existing containers..."
docker-compose down

echo "🧹 Clearing Docker build cache..."
docker builder prune -f

echo "🏗 Rebuilding and starting containers with hot reloading..."
docker-compose up --build

echo "✅ Done! Your containers should now auto-refresh when code changes."
