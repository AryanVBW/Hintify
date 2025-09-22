#!/bin/bash

echo "=== Hintify Development Environment Test ==="
echo ""

# Check if both servers are running
echo "1. Checking if website is running on localhost:3000..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Website is running on http://localhost:3000"
else
    echo "   ❌ Website is NOT running. Please run: cd Hintidy_website && npm run dev"
fi

echo ""
echo "2. Checking Electron app development mode..."
if pgrep -f "NODE_ENV=development electron" > /dev/null; then
    echo "   ✅ Electron app is running in development mode"
    echo "   📝 Auth redirects will use: http://localhost:3000/auth-success?source=app"
else
    echo "   ❌ Electron app is NOT running in dev mode. Please run: cd Hintify_app && npm run dev"
fi

echo ""
echo "3. Environment Configuration:"
echo "   Development:"
echo "   - Electron: npm run dev"
echo "   - Website: npm run dev (port 3000)"
echo "   - Auth URL: http://localhost:3000/auth-success?source=app"
echo ""
echo "   Production:"
echo "   - Electron: npm start (or built app)"
echo "   - Website: Deployed to Vercel"
echo "   - Auth URL: https://hintify.vercel.app/auth-success?source=app"

echo ""
echo "=== Test Complete ==="