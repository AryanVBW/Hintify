# Hintify Authentication Integration

This document explains how the authentication system works between the Hintify Electron app and the Hintify website.

## Overview

The Hintify project now requires users to sign in before using the application. The authentication flow is:

1. **Electron App** → Shows authentication screen if user is not signed in
2. **Sign In Button** → Opens the website in browser for authentication  
3. **Website Authentication** → User signs in with Clerk
4. **Deep Link Redirect** → Website redirects back to Electron app with auth data
5. **App Authorization** → Electron app receives auth data and shows main interface

## Components

### Electron App (`Hintify_app/`)

#### Authentication Screen
- **File**: `src/renderer/auth.html`
- **Styling**: `src/renderer/auth.css` 
- **Logic**: `src/renderer/auth.js`

Features:
- Beautiful dark theme matching app design
- Animated background elements
- Clear benefit explanations
- Sign-in button that opens website

#### Main Process Updates
- **File**: `src/main.js`
- Added authentication status checking
- Deep link protocol registration (`hintify://`)
- Authentication window management
- User data persistence

#### Protocol Registration
- **File**: `package.json`
- Registered `hintify://` protocol for deep linking
- Single instance enforcement for better link handling

### Website (`Hintidy_website/`)

#### Authentication Success Page
- **File**: `app/auth-success/page.tsx`
- Shows user welcome message
- Provides "Open App" button with deep link
- Handles both app and web flows
- Fallback for app download

#### Protected Routes
- **File**: `middleware.ts`
- Dashboard routes protected with Clerk
- Automatic redirect to sign-in for unauthenticated users

#### Navbar Updates
- **File**: `components/ui/navbar.tsx`
- Shows sign-in/sign-up buttons when not authenticated
- Shows user profile button when authenticated
- Links to protected dashboard

## Authentication Flow

### 1. App Startup
```javascript
// main.js - Always show main window, handle auth internally
const authStatus = checkAuthStatus();
createMainWindow();

// Main window handles authentication state internally
if (mainWindow) {
    mainWindow.show();
}
```

### 2. Main App UI States

**When NOT authenticated:**
- "Sign In" button visible in top-right corner
- Authentication message displayed in main content area
- App menu shows "Sign In..." option
- Capture and other features remain visible but require auth

**When authenticated:**
- User avatar and name shown in top-right corner
- Normal app functionality available in main area
- App menu shows "Sign Out (username)" option
- All features fully functional

### 3. Sign-In Process
```javascript
// renderer.js - Sign in from main app overlay
function handleSignIn() {
    // Send message to main process to show auth window
    ipcRenderer.send('show-auth-window');
}

// auth.js - Automatically detects environment
const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--development');
const websiteUrl = isDev 
    ? 'http://localhost:3000/auth-success?source=app'  // Development
    : 'https://hintify.vercel.app/auth-success?source=app'; // Production

shell.openExternal(websiteUrl);
```

### 3. Deep Link Return
```javascript
// main.js - Handle deep link from website
app.on('open-url', (event, url) => {
    handleDeepLink(url); // Process auth data
});

// Example deep link:
// hintify://auth-success?userId=123&email=user@example.com&name=John%20Doe
```

### 4. Authentication Storage
```javascript
// Store auth data locally
store.set('user_authenticated', true);
store.set('user_info', {
    id: userData.id,
    email: userData.email,
    name: userData.name,
    imageUrl: userData.imageUrl
});
```

### 5. UI Updates
```javascript
// renderer.js - Update UI based on auth status
function updateAuthUI(isAuthenticated, userData = null) {
    const authBtn = document.getElementById('auth-btn');
    const userInfoDiv = document.getElementById('user-info');
    
    if (isAuthenticated && userData) {
        authBtn.classList.add('hidden');
        userInfoDiv.classList.remove('hidden');
        // Update user avatar and name
    } else {
        authBtn.classList.remove('hidden');
        userInfoDiv.classList.add('hidden');
    }
}
```

## Setup Instructions

### 1. Website Setup (Clerk)
1. Create a Clerk account at [clerk.com](https://clerk.com)
2. Create a new Clerk application
3. Copy your publishable and secret keys
4. Create `.env.local` in `Hintidy_website/`:
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_key_here
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/auth-success?source=web
```

### 2. Development Setup
```bash
# Terminal 1 - Start website
cd Hintidy_website
npm install
npm run dev   # Runs on http://localhost:3000

# Terminal 2 - Start Electron app in development mode
cd Hintify_app
npm install
npm run dev   # Uses localhost for auth redirect
```

**Important**: Use `npm run dev` for the Electron app during development. This:
- Sets `NODE_ENV=development`
- Adds `--development` flag
- Automatically redirects to `http://localhost:3000` instead of production URL
- Enables better debugging and logging

## Development vs Production

### Development Mode
- **Command**: `npm run dev` (Electron app)
- **Website URL**: `http://localhost:3000`
- **Environment**: `NODE_ENV=development`
- **Features**: Debug logging, DevTools, localhost redirects

### Production Mode  
- **Command**: `npm start` or built app
- **Website URL**: `https://hintify.vercel.app`
- **Environment**: Production
- **Features**: Optimized performance, production URLs

The app automatically detects the environment and uses the appropriate URLs.

### 3. Production Setup
For production, update the website URL in `auth.js`:
```javascript
const websiteUrl = 'https://hintify.vercel.app/auth-success?source=app';
```

## Testing

### Manual Testing
1. Start both website and Electron app
2. Electron app should show authentication screen
3. Click "Sign In with Hintify" button
4. Website opens in browser
5. Complete sign-in process
6. Click "Open Hintify App" button
7. App should authenticate and show main interface

### Deep Link Testing
Run the test script:
```bash
./test-deep-link.sh
```

Or manually test a deep link:
```bash
open "hintify://auth-success?userId=test123&email=test@example.com&name=Test%20User"
```

## File Structure

```
Hintify_app/
├── src/
│   ├── main.js                 # Main process with auth logic
│   └── renderer/
│       ├── auth.html          # Authentication screen UI
│       ├── auth.css           # Authentication screen styles  
│       ├── auth.js            # Authentication screen logic
│       └── ...
└── package.json               # Protocol registration

Hintidy_website/
├── app/
│   ├── auth-success/
│   │   └── page.tsx           # Post-auth redirect page
│   ├── dashboard/
│   │   └── page.tsx           # Protected dashboard
│   └── ...
├── middleware.ts              # Route protection
└── .env.local.example         # Environment variables template
```

## Security Notes

- User credentials are never stored in the Electron app
- Authentication is handled entirely by Clerk on the website
- Only basic user info (ID, email, name, avatar) is passed via deep link
- Local storage only contains user identification, not sensitive data
- Deep links are validated and parsed securely

## Troubleshooting

### App Won't Open from Website
1. Ensure Electron app is installed and has run at least once
2. Check if `hintify://` protocol is registered in system
3. Try running the deep link test script
4. Check Electron app console for deep link logs

### Authentication Not Persisting
1. Check if user data is being stored in electron-store
2. Verify deep link parameters are being parsed correctly
3. Ensure auth status check is working in main.js

### Website Authentication Issues
1. Verify Clerk environment variables are set correctly
2. Check Clerk dashboard for application configuration
3. Ensure middleware is protecting routes properly

## Future Enhancements

- [ ] Add user profile management in app
- [ ] Implement authentication refresh/logout
- [ ] Add user preferences sync between app and website
- [ ] Enhanced error handling for network issues
- [ ] OAuth provider integration (Google, GitHub, etc.)