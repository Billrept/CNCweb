#!/bin/zsh

echo "🔄 Restarting containers with bug fix..."
docker-compose down
docker-compose up --build

echo "✅ Done! The app should now be running with the bug fix."
