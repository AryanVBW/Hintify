#!/bin/bash

echo "🧪 Testing Onboarding Wizard"
echo "============================="
echo ""

echo "1. Clearing onboarding status to simulate first run..."

# Clear the electron-store data to simulate first run
echo "   Removing app data to force onboarding..."

# macOS app data location
APP_DATA_PATH="$HOME/Library/Application Support/hintify-snapassist-ai"
if [ -d "$APP_DATA_PATH" ]; then
    echo "   Found app data at: $APP_DATA_PATH"
    echo "   Removing config.json to reset onboarding..."
    rm -f "$APP_DATA_PATH/config.json"
    echo "   ✅ App data cleared"
else
    echo "   ℹ️  No existing app data found (first run)"
fi

echo ""
echo "2. What should happen now:"
echo "   - Start the app with: npm run dev"
echo "   - App should show onboarding wizard"
echo "   - Main window should be hidden initially"
echo "   - After completing setup, main window should appear"

echo ""
echo "3. Manual Test Steps:"
echo "   □ 1. Run: cd Hintify_app && npm run dev"
echo "   □ 2. Onboarding wizard should appear automatically"
echo "   □ 3. Main window should be hidden"
echo "   □ 4. Complete the setup wizard"
echo "   □ 5. Main window should appear after setup"
echo "   □ 6. Check logs for 'First run detected' message"

echo ""
echo "4. Debug Information:"
echo "   Look for these log messages:"
echo "   - 'App setup: {isFirstRun: true}'"
echo "   - 'First run detected - showing onboarding wizard'"
echo "   - 'Onboarding completed with config:'"

echo ""
echo "============================="
echo "Ready to test! Run the app now."