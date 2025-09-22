#!/usr/bin/env node

/**
 * Comprehensive Test Script for Hintify Authentication & Database Integration
 * This script tests the complete flow from authentication to data transfer
 */

const path = require('path');
process.chdir(path.join(__dirname, 'Hintify_app'));

const AuthService = require('./Hintify_app/src/services/AuthService');
const DatabaseService = require('./Hintify_app/src/services/DatabaseService');
const PortalDataTransferService = require('./Hintify_app/src/services/PortalDataTransferService');
require('dotenv').config();

class HintifyTester {
  constructor() {
    this.authService = new AuthService();
    this.dbService = new DatabaseService();
    this.portalService = new PortalDataTransferService();
    this.testUserId = null;
    this.testSessionId = null;
  }

  async runAllTests() {
    console.log('🧪 Starting Hintify Integration Tests\n');
    
    try {
      await this.testDatabaseConnection();
      await this.testUserAuthentication();
      await this.testSessionManagement();
      await this.testQuestionAnswerFlow();
      await this.testUsageTracking();
      await this.testDataExport();
      await this.testPortalTransfer();
      await this.cleanup();
      
      console.log('\n🎉 All tests passed successfully!');
      console.log('✅ Hintify authentication and database integration is working correctly.');
      
    } catch (error) {
      console.error('\n❌ Test failed:', error.message);
      console.error(error);
      await this.cleanup();
      process.exit(1);
    }
  }

  async testDatabaseConnection() {
    console.log('📡 Testing database connection...');
    
    try {
      const result = await this.dbService.sql`SELECT 1 as test, NOW() as timestamp`;
      console.log('✅ Database connection successful');
      console.log(`   Connected at: ${result[0].timestamp}`);
    } catch (error) {
      throw new Error(`Database connection failed: ${error.message}`);
    }
  }

  async testUserAuthentication() {
    console.log('\n🔐 Testing user authentication...');
    
    const testUserData = {
      userId: 'test-user-123',
      email: 'test.user@hintify.app',
      name: 'Test User',
      firstName: 'Test',
      lastName: 'User',
      username: 'testuser',
      imageUrl: 'https://example.com/avatar.jpg',
      provider: 'test'
    };
    
    try {
      const authResult = await this.authService.processAuthentication(testUserData);
      this.testUserId = authResult.user.id;
      this.testSessionId = authResult.session.id;
      
      console.log('✅ User authentication successful');
      console.log(`   User ID: ${this.testUserId}`);
      console.log(`   Session ID: ${this.testSessionId}`);
      
      // Test user retrieval
      const retrievedUser = await this.dbService.getUserByEmail(testUserData.email);
      if (!retrievedUser) {
        throw new Error('User not found after creation');
      }
      
      console.log('✅ User retrieval successful');
      
    } catch (error) {
      throw new Error(`User authentication failed: ${error.message}`);
    }
  }

  async testSessionManagement() {
    console.log('\n📱 Testing session management...');
    
    try {
      // Get active session
      const activeSession = await this.dbService.getActiveSession(this.testUserId);
      if (!activeSession) {
        throw new Error('No active session found');
      }
      
      console.log('✅ Active session found');
      console.log(`   Session ID: ${activeSession.id}`);
      
      // Test session ending
      await this.dbService.endAppSession(this.testSessionId);
      console.log('✅ Session ended successfully');
      
      // Start new session for remaining tests
      const newSessionId = await this.dbService.startAppSession(
        this.testUserId,
        { platform: 'test', version: '1.0.0' },
        '1.0.0-test'
      );
      this.testSessionId = newSessionId;
      console.log('✅ New session started for testing');
      
    } catch (error) {
      throw new Error(`Session management failed: ${error.message}`);
    }
  }

  async testQuestionAnswerFlow() {
    console.log('\n❓ Testing question and answer flow...');
    
    try {
      const questionText = 'What is the capital of France?';
      const answerText = `Hint 1: It's known as the City of Light\nHint 2: It's located on the Seine River\nHint 3: Home to the Eiffel Tower`;
      
      const { questionId, answerId } = await this.authService.saveQuestionAnswer(
        questionText,
        answerText,
        'text',
        'test',
        'test-model',
        null,
        { difficulty: 'easy', category: 'geography' },
        1500
      );
      
      console.log('✅ Question and answer saved successfully');
      console.log(`   Question ID: ${questionId}`);
      console.log(`   Answer ID: ${answerId}`);
      
      // Test with image question
      const imageQuestionId = await this.dbService.saveQuestion(
        this.testUserId,
        this.testSessionId,
        'Solve this math equation from the image',
        'image_ocr',
        'base64_image_data_here',
        { ocr_confidence: 0.95 }
      );
      
      console.log('✅ Image question saved successfully');
      
    } catch (error) {
      throw new Error(`Question/Answer flow failed: ${error.message}`);
    }
  }

  async testUsageTracking() {
    console.log('\n📊 Testing usage tracking...');
    
    try {
      // Test various usage events
      const usageEvents = [
        { feature: 'screenshot', action: 'captured', details: { method: 'button' } },
        { feature: 'clipboard', action: 'processed', details: { image_size: 1024 } },
        { feature: 'settings', action: 'opened', details: null },
        { feature: 'ai_processing', action: 'completed', details: { provider: 'gemini', time: 2000 } }
      ];
      
      for (const event of usageEvents) {
        await this.authService.logActivity(event.feature, event.action, event.details);
      }
      
      console.log('✅ Usage tracking events logged successfully');
      console.log(`   Logged ${usageEvents.length} different usage events`);
      
    } catch (error) {
      throw new Error(`Usage tracking failed: ${error.message}`);
    }
  }

  async testDataExport() {
    console.log('\n📤 Testing data export...');
    
    try {
      // Test JSON export
      const jsonExport = await this.authService.exportUserData('json');
      if (!jsonExport.data || !jsonExport.filename) {
        throw new Error('JSON export data incomplete');
      }
      
      console.log('✅ JSON export successful');
      console.log(`   Filename: ${jsonExport.filename}`);
      console.log(`   Data size: ${JSON.stringify(jsonExport.data).length} characters`);
      
      // Test CSV export
      const csvExport = await this.authService.exportUserData('csv');
      if (!csvExport.data || !csvExport.filename) {
        throw new Error('CSV export data incomplete');
      }
      
      console.log('✅ CSV export successful');
      console.log(`   Filename: ${csvExport.filename}`);
      console.log(`   Data size: ${csvExport.data.length} characters`);
      
    } catch (error) {
      throw new Error(`Data export failed: ${error.message}`);
    }
  }

  async testPortalTransfer() {
    console.log('\n🚀 Testing Portal data transfer...');
    
    try {
      // Test Portal connectivity (may fail if Portal is not available)
      const isPortalOnline = await this.portalService.checkPortalConnectivity();
      console.log(`   Portal connectivity: ${isPortalOnline ? 'Online' : 'Offline'}`);
      
      // Test data transfer (will queue if Portal is offline)
      const transferResult = await this.authService.transferDataToPortal();
      
      if (transferResult.success) {
        console.log('✅ Portal data transfer successful');
        console.log(`   Transfer ID: ${transferResult.transferId}`);
        
        if (transferResult.queued) {
          console.log('   Transfer queued for when Portal becomes available');
        }
      } else {
        console.log('⚠️  Portal transfer failed (expected if Portal is offline)');
        console.log(`   Error: ${transferResult.error}`);
      }
      
    } catch (error) {
      console.log('⚠️  Portal transfer test failed (expected if Portal is offline)');
      console.log(`   Error: ${error.message}`);
    }
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up test data...');
    
    try {
      if (this.testUserId) {
        // Delete test user and related data (cascading deletes will handle related records)
        await this.dbService.sql`
          DELETE FROM app_data.users WHERE id = ${this.testUserId}
        `;
        console.log('✅ Test user and related data cleaned up');
      }
    } catch (error) {
      console.error('⚠️  Cleanup failed:', error.message);
    }
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new HintifyTester();
  tester.runAllTests();
}

module.exports = HintifyTester;