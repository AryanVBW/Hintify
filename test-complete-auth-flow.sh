#!/bin/bash

# Complete authentication flow test for Hintify
# This script tests the entire authentication flow from website to app

echo "🧪 Hintify Complete Authentication Flow Test"
echo "============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if processes are running
check_process() {
    local process_name="$1"
    local port="$2"
    
    if [ -n "$port" ]; then
        if lsof -i ":$port" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $process_name is running on port $port"
            return 0
        else
            echo -e "${RED}✗${NC} $process_name is not running on port $port"
            return 1
        fi
    else
        if pgrep -f "$process_name" > /dev/null; then
            echo -e "${GREEN}✓${NC} $process_name is running"
            return 0
        else
            echo -e "${RED}✗${NC} $process_name is not running"
            return 1
        fi
    fi
}

echo "1. Environment Check:"
echo "---------------------"

# Check if website is running
check_process "next-server" "3000"
WEBSITE_RUNNING=$?

# Check if Electron app is built
if [ -f "Hintify_app/dist/mac/Hintify SnapAssist AI.app/Contents/MacOS/Hintify SnapAssist AI" ]; then
    echo -e "${GREEN}✓${NC} Electron app is built"
    APP_BUILT=0
else
    echo -e "${YELLOW}⚠${NC} Electron app needs to be built"
    APP_BUILT=1
fi

echo ""
echo "2. Authentication Flow Test Instructions:"
echo "----------------------------------------"

echo ""
echo -e "${BLUE}Step 1: Start the website (if not running)${NC}"
if [ $WEBSITE_RUNNING -ne 0 ]; then
    echo "  cd Hintidy_website && npm run dev"
    echo "  Wait for it to start on http://localhost:3000"
else
    echo "  Website is already running ✓"
fi

echo ""
echo -e "${BLUE}Step 2: Build/Start the Electron app${NC}"
if [ $APP_BUILT -ne 0 ]; then
    echo "  cd Hintify_app && npm run build-mac-dev"
    echo "  Then run the built app"
else
    echo "  Run: cd Hintify_app && npm run dev"
    echo "  Or open the built app from dist/"
fi

echo ""
echo -e "${BLUE}Step 3: Manual Authentication Flow Test${NC}"
echo "  1. Open the Electron app"
echo "  2. You should see 'Sign In' button in top-right corner"
echo "  3. Click 'Sign In' - it should open your browser to:"
echo "     http://localhost:3000/auth-success?source=app"
echo "  4. Complete sign-in on the website"
echo "  5. After sign-in, the website should automatically redirect to the app"
echo "  6. The app should show user info in top-right instead of Sign In"
echo "  7. Main area should show welcome message and system readiness"

echo ""
echo -e "${BLUE}Step 4: Deep Link Test (Alternative)${NC}"
echo "  Run: ./Hintify_app/test-auth-deeplink.sh"
echo "  This simulates the website sending auth data to the app"

echo ""
echo "3. Expected Results:"
echo "-------------------"
echo -e "${GREEN}✓${NC} App shows user avatar and name in top-right corner"
echo -e "${GREEN}✓${NC} App menu shows 'Sign Out (username)' option"
echo -e "${GREEN}✓${NC} Main area shows welcome message instead of auth message"
echo -e "${GREEN}✓${NC} Status shows 'Authentication successful! Ready to process images.'"
echo -e "${GREEN}✓${NC} User can now use screenshot capture and clipboard processing"

echo ""
echo "4. Debug Information:"
echo "--------------------"
echo "If authentication fails, check:"
echo "  • Open DevTools in the app (F12) to see console logs"
echo "  • Check browser console on the website"
echo "  • Verify the deep link format matches expected parameters"
echo "  • Ensure electron-store is saving user data properly"

echo ""
echo "5. Troubleshooting:"
echo "------------------"
echo "If app doesn't open from website:"
echo "  • Run: defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add '{LSHandlerContentType=hintify;LSHandlerRoleAll=com.hintify.snapassist-ai;}'"
echo "  • Or test manually with: open 'hintify://auth-success?userId=test&email=test@example.com&name=Test%20User'"

echo ""
echo "6. Quick Test:"
echo "-------------"
read -p "Do you want to run a quick deep link test now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running deep link test..."
    if [ -f "Hintify_app/test-auth-deeplink.sh" ]; then
        cd Hintify_app && ./test-auth-deeplink.sh
    else
        echo -e "${RED}✗${NC} test-auth-deeplink.sh not found"
    fi
fi

echo ""
echo -e "${GREEN}Test guide completed!${NC}"
echo "Follow the steps above to verify your authentication flow."