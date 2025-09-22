#!/bin/bash

echo "🧪 Testing Hintify Authentication Integration"
echo "=============================================="
echo ""

# Check if both services are running
echo "1. Service Status Check:"
echo "-----------------------"

if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Website running on http://localhost:3000"
else
    echo "   ❌ Website NOT running - Please run: cd Hintidy_website && npm run dev"
    echo ""
    echo "To start website:"
    echo "cd /Volumes/DATA_vivek/GITHUB/Hintify/hindify-js/Hintidy_website"
    echo "npm run dev"
    echo ""
fi

if pgrep -f "NODE_ENV=development electron" > /dev/null; then
    echo "   ✅ Electron app running in development mode"
else
    echo "   ❌ Electron app NOT running in dev mode"
    echo ""
    echo "To start app:"
    echo "cd /Volumes/DATA_vivek/GITHUB/Hintify/hindify-js/Hintify_app"
    echo "npm run dev"
    echo ""
fi

echo ""
echo "2. Authentication Flow Test:"
echo "---------------------------"

echo "📋 Manual Test Checklist:"
echo ""
echo "□ 1. Open Electron app - should show main window"
echo "□ 2. Check top-right corner for 'Sign In' button"
echo "□ 3. Main content should show authentication message"
echo "□ 4. Click 'Sign In' button → should open website auth page"
echo "□ 5. Complete sign-in on website"
echo "□ 6. Click 'Open App' on website → should return to app"
echo "□ 7. App should now show user info instead of Sign In button"
echo "□ 8. Main content should show normal functionality"
echo "□ 9. Test menu: App → Sign Out should work"
echo "□ 10. Test menu: App → Sign In should work when logged out"

echo ""
echo "3. Expected URLs for Development:"
echo "--------------------------------"
echo "   Website: http://localhost:3000"
echo "   Auth Success: http://localhost:3000/auth-success?source=app"
echo "   Deep Link: hintify://auth-success?userId=...&email=...&name=..."

echo ""
echo "4. UI Elements to Verify:"
echo "-------------------------"
echo "   When NOT authenticated:"
echo "   - 'Sign In' button visible in top-right"
echo "   - Authentication message in main area"
echo "   - Menu shows 'Sign In...' option"
echo ""
echo "   When authenticated:"
echo "   - User avatar and name visible in top-right"
echo "   - Normal app functionality in main area"
echo "   - Menu shows 'Sign Out (username)' option"

echo ""
echo "5. Deep Link Test:"
echo "------------------"
echo "   To test deep linking manually:"
echo "   open \"hintify://auth-success?userId=test123&email=test@example.com&name=Test%20User\""

echo ""
echo "=============================================="
echo "🎯 Test completed! Follow the checklist above to verify functionality."