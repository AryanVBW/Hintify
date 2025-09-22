#!/usr/bin/env node

/**
 * Database Setup Script for Hintify
 * This script initializes the Neon database with the required schema
 */

const { neon } = require('@neondatabase/serverless');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function setupDatabase() {
  console.log('🚀 Starting Hintify database setup...');
  
  // Check if DATABASE_URL is configured
  if (!process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL not found in environment variables');
    console.log('Please ensure your .env.local file contains the DATABASE_URL');
    process.exit(1);
  }
  
  try {
    // Initialize Neon connection
    const sql = neon(process.env.DATABASE_URL);
    
    console.log('📡 Connecting to Neon database...');
    
    // Test connection
    await sql`SELECT 1 as test`;
    console.log('✅ Database connection successful');
    
    // Read schema file
    const schemaPath = path.join(__dirname, 'database_schema.sql');
    
    if (!fs.existsSync(schemaPath)) {
      console.error('❌ Database schema file not found:', schemaPath);
      process.exit(1);
    }
    
    const schemaSQL = fs.readFileSync(schemaPath, 'utf8');
    
    console.log('📚 Executing database schema...');
    
    // Split SQL into individual statements
    const statements = schemaSQL
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));
    
    console.log(`📝 Executing ${statements.length} SQL statements...`);
    
    // Execute each statement
    for (let i = 0; i < statements.length; i++) {
      try {
        await sql.unsafe(statements[i]);
        console.log(`✅ Statement ${i + 1}/${statements.length} executed successfully`);
      } catch (error) {
        console.error(`❌ Error executing statement ${i + 1}:`, error.message);
        console.log('Statement:', statements[i].substring(0, 100) + '...');
        throw error;
      }
    }
    
    console.log('🎉 Database schema setup completed successfully!');
    
    // Test the setup by creating a test user
    console.log('🧪 Testing database setup...');
    
    const testResult = await sql`
      SELECT app_data.create_or_update_user(
        'test-user-id',
        'test@hintify.app',
        'Test User',
        'Test',
        'User',
        'testuser',
        null,
        'test'
      ) AS user_id
    `;
    
    console.log('✅ Test user created with ID:', testResult[0].user_id);
    
    // Clean up test user
    await sql`DELETE FROM app_data.users WHERE email = 'test@hintify.app'`;
    console.log('✅ Test user cleaned up');
    
    console.log('\n🎯 Database setup completed successfully!');
    console.log('🔗 Your database is ready for Hintify authentication and data storage.');
    
  } catch (error) {
    console.error('❌ Database setup failed:', error.message);
    console.error(error);
    process.exit(1);
  }
}

// Run setup if called directly
if (require.main === module) {
  setupDatabase();
}

module.exports = { setupDatabase };