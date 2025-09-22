# Hintify Authentication & Database Integration Guide

This guide explains how to set up and use the integrated Neon database authentication system with Hintify.

## Overview

Hintify now includes:
- **Neon Database Integration**: PostgreSQL database for storing user data, questions, answers, and usage analytics
- **Stack Auth Integration**: Modern authentication system with JWT tokens
- **Portal Data Transfer**: Automatic data synchronization to Hintify Portal
- **User Dashboard**: Track questions, answers, and usage history
- **Data Export**: Export user data in JSON or CSV format

## Database Schema

The system creates the following tables in the `app_data` schema:

### Core Tables
- **`users`**: User profile information and authentication data
- **`app_sessions`**: User session tracking for analytics
- **`questions`**: All user questions with metadata
- **`answers`**: AI-generated responses with performance metrics
- **`app_usage`**: Feature usage tracking for insights
- **`data_transfers`**: Portal synchronization history

### Key Features
- Automatic timestamps and UUIDs
- Foreign key relationships for data integrity
- Indexes for optimal query performance
- Helper functions for common operations

## Setup Instructions

### 1. Environment Configuration

Your `.env.local` file should contain:

```bash
# Neon Database Configuration
DATABASE_URL=\"postgresql://neondb_owner:npg_Mxg5Xq4LlVrc@ep-divine-truth-afqnj5es-pooler.c-2.us-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require\"
NEON_PROJECT_ID=\"super-queen-66007382\"
NEON_BRANCH_ID=\"br-silent-river-afq4gxqz\"

# Neon Auth Configuration
NEXT_PUBLIC_STACK_PROJECT_ID='f13a07b6-29d7-4dcd-bfeb-9315e40fd9e0'
NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY='pck_yabj98p1bskthpzfz731m7466mrhk5n7rpetcbryx8xz8'
STACK_SECRET_SERVER_KEY='ssk_zfbpw0p2a0cf72tr3cqwb1jyh5ee2xw3825gpjqj21gq0'

# JWKS URL for JWT verification
STACK_JWKS_URL='https://api.stack-auth.com/api/v1/projects/f13a07b6-29d7-4dcd-bfeb-9315e40fd9e0/.well-known/jwks.json'

# Portal Configuration
PORTAL_API_URL=\"https://portal.hintify.app/api\"
PORTAL_DATA_TRANSFER_ENDPOINT=\"/data-transfer\"
```

### 2. Database Setup

Run the database setup script:

```bash
# Option 1: Using the shell script (requires psql)
./setup-database.sh

# Option 2: Manual setup using psql
psql \"$DATABASE_URL\" -f database_schema.sql
```

### 3. Install Dependencies

Make sure all required packages are installed:

```bash
# In the Hintify_app directory
cd Hintify_app
npm install @neondatabase/serverless pg dotenv jsonwebtoken

# In the Hintidy_website directory
cd ../Hintidy_website
npm install @neondatabase/serverless pg dotenv jsonwebtoken
```

## Authentication Flow

### 1. User Sign-In
1. User clicks \"Sign In\" button in the app
2. App opens Hintify website in browser
3. User completes authentication on website
4. Website redirects to `hintify://auth-success` with user data
5. App processes the deep link and authenticates user
6. User profile is created/updated in database
7. App session is started for analytics

### 2. Session Management
- Each app launch creates a new session
- Sessions track device info, app version, and duration
- Previous sessions are automatically ended when new ones start
- Session data is used for usage analytics

## Data Management Features

### Question & Answer Tracking
- Every question and AI response is automatically saved
- Includes processing time, AI provider, and confidence metrics
- Questions are linked to user sessions for context
- Supports text, image, and OCR question types

### Usage Analytics
- Tracks all feature usage (screenshots, clipboard, settings, etc.)
- Records timestamps, session context, and action details
- Provides insights into user behavior and app performance
- Used for improving user experience

### Portal Data Transfer
- Automatic background sync every 5 minutes
- Manual transfer via user menu dropdown
- Handles offline scenarios with queue system
- Includes comprehensive user data summary

### Data Export
- Export as JSON: Complete data with metadata
- Export as CSV: Question/answer pairs for analysis
- Includes user stats and activity summaries
- Download directly from app interface

## User Interface Features

### Authentication UI
- Sign-in button when not authenticated
- User avatar and name when authenticated
- Dropdown menu with data management options
- Authentication status in welcome messages

### User Menu Options
- **Transfer to Portal**: Sync data to Hintify Portal
- **Export as JSON**: Download complete data archive
- **Export as CSV**: Download spreadsheet-friendly format
- **View History**: Browse questions and answers
- **Sign Out**: Clear authentication and end session

### History Modal
- Browse all previous questions and answers
- Filter by date and AI provider
- View processing times and metadata
- Grouped by question with multiple answers

## API Reference

### Main Process (IPC Handlers)

```javascript
// Save question and answer
ipcRenderer.invoke('save-question-answer', {
  questionText: 'What is 2+2?',
  answerText: 'Here are some hints...',
  questionType: 'text',
  aiProvider: 'gemini',
  aiModel: 'gemini-2.0-flash',
  processingTime: 1500
})

// Transfer data to Portal
ipcRenderer.invoke('transfer-data-to-portal')

// Export user data
ipcRenderer.invoke('export-user-data', 'json')

// Get user history
ipcRenderer.invoke('get-user-history', 50)

// Log activity
ipcRenderer.invoke('log-activity', 'screenshot', 'captured', { size: 1024 })
```

### Database Service Methods

```javascript
const dbService = new DatabaseService();

// User management
const userId = await dbService.createOrUpdateUser(userData);
const user = await dbService.getUserByEmail('user@example.com');

// Session management
const sessionId = await dbService.startAppSession(userId, deviceInfo, appVersion);
await dbService.endAppSession(sessionId);

// Questions and answers
const questionId = await dbService.saveQuestion(userId, sessionId, text, type);
const answerId = await dbService.saveAnswer(questionId, userId, text, provider, model);

// Usage tracking
await dbService.logUsage(userId, sessionId, 'feature', 'action', details);

// Data retrieval
const summary = await dbService.getUserDataSummary(userId);
const history = await dbService.getUserHistory(userId, limit);
```

### Portal Transfer Service

```javascript
const portalService = new PortalDataTransferService();

// Transfer data
const result = await portalService.transferUserDataToPortal(userId);

// Export data
const exportData = await portalService.exportUserData(userId, 'json');

// Check connectivity
const isOnline = await portalService.checkPortalConnectivity();

// Sync pending transfers
await portalService.syncPendingTransfers();
```

## Security Features

### Authentication Security
- JWT token validation with public key verification
- JWKS endpoint for key rotation support
- Secure token storage in electron-store
- Deep link validation and sanitization

### Database Security
- Parameterized queries to prevent SQL injection
- UUID primary keys for security through obscurity
- Foreign key constraints for data integrity
- Prepared statements for all database operations

### Data Privacy
- User data is only stored with explicit consent
- Local storage with optional cloud sync
- Data export and deletion capabilities
- GDPR-compliant data handling

## Troubleshooting

### Common Issues

**Database Connection Failed**
- Check DATABASE_URL in .env.local
- Verify Neon project is active
- Test connection with psql

**Authentication Not Working**
- Verify Stack Auth configuration
- Check deep link protocol registration
- Ensure website redirects to correct scheme

**Data Not Saving**
- Check user authentication status
- Verify database schema is set up
- Look for errors in console logs

**Portal Transfer Failing**
- Check internet connectivity
- Verify Portal API endpoint
- Review transfer history for error messages

### Debug Mode

Enable debug logging:

```bash
# Run app with development flags
npm run dev

# Check console logs in DevTools
# Main process logs in terminal
# Renderer process logs in DevTools
```

### Database Inspection

```sql
-- Check user data
SELECT * FROM app_data.users ORDER BY created_at DESC LIMIT 5;

-- Check recent questions
SELECT * FROM app_data.questions ORDER BY created_at DESC LIMIT 10;

-- Check app usage
SELECT feature_name, action, COUNT(*) 
FROM app_data.app_usage 
GROUP BY feature_name, action 
ORDER BY COUNT(*) DESC;

-- Check data transfers
SELECT * FROM app_data.data_transfers ORDER BY created_at DESC LIMIT 5;
```

## Future Enhancements

### Planned Features
- Real-time sync with WebSocket connections
- Advanced analytics dashboard
- Machine learning model training on user data
- Multi-device session synchronization
- Enhanced data visualization

### API Extensions
- GraphQL API for flexible data queries
- Webhook support for real-time notifications
- Third-party integrations (Google Classroom, etc.)
- Advanced search and filtering capabilities

This comprehensive system provides a solid foundation for user data management, authentication, and analytics while maintaining privacy and security standards.