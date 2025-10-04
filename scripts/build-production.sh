#!/bin/bash

# Build script for production deployment of co.nnecti.ng

echo "🚀 Building co.nnecti.ng for production deployment..."

# Set production environment variables
export NODE_ENV=production
export REACT_APP_API_URL=https://api.co.nnecti.ng

# Navigate to frontend directory
cd frontend

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building production bundle..."
npm run build

echo "✅ Production build completed!"
echo ""
echo "📋 Deployment instructions:"
echo "1. Upload the 'frontend/build' directory to your web server"
echo "2. Configure your web server to serve the static files"
echo "3. Set up reverse proxy for API calls to your Flask backend"
echo "4. Ensure your Flask backend is running and accessible at the configured API URL"
echo ""
echo "🌐 Frontend will connect to: $REACT_APP_API_URL"
