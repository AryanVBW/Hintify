#!/bin/bash

# Test script for Hintify deep linking
echo "Testing Hintify Deep Link..."

# Test deep link URL
DEEP_LINK="hintify://auth-success?userId=test123&email=test@example.com&name=Test%20User&imageUrl=https://example.com/avatar.jpg"

echo "Opening deep link: $DEEP_LINK"

# On macOS, use open command
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$DEEP_LINK"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$DEEP_LINK"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    start "$DEEP_LINK"
else
    echo "Unsupported OS: $OSTYPE"
    echo "Please manually test the deep link: $DEEP_LINK"
fi

echo "Deep link test completed. Check if the Hintify app opened and authenticated."