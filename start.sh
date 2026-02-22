#!/bin/bash
# start.sh - Emergency manual deployment script for F&O Sentinel
# This bypasses the buggy Docker Compose v1.29 'ContainerConfig' error

echo "🛑 Stopping existing containers..."
docker stop fno_sentinel_prod fno_nginx_prod 2>/dev/null
docker rm -f fno_sentinel_prod fno_nginx_prod 2>/dev/null

echo "🧹 Cleaning up stale images and networks..."
docker network rm fno_network 2>/dev/null
docker network create fno_network

echo "🏗️ Building Backend Image..."
docker build -t fno-sentinel-img -f Dockerfile.web .

echo "🚀 Starting Backend Container..."
# Note: Using a local folder for data to ensure we can easily wipe it if schema mismatches
mkdir -p $(pwd)/data $(pwd)/logs
docker run -d \
  --name fno_sentinel_prod \
  --network fno_network \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  -e DATABASE_URL=sqlite:////app/data/trading.db \
  --restart always \
  fno-sentinel-img

echo "🌐 Starting Nginx Proxy..."
docker run -d \
  --name fno_nginx_prod \
  --network fno_network \
  -p 8080:80 \
  -v $(pwd)/web/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  --link fno_sentinel_prod:fno-sentinel \
  --restart always \
  nginx:alpine

echo "✅ Deployment Complete!"
echo "Visit: http://76.13.179.32:8080/register"
echo "------------------------------------------------"
echo "If you still see a 500 error, run: rm -rf data/trading.db"
echo "------------------------------------------------"
