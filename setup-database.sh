#!/bin/bash

# Hintify Database Setup Script
# This script sets up the Neon database schema using psql

echo "🚀 Setting up Hintify database schema..."

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "❌ .env.local file not found"
    echo "Please create .env.local with your database credentials"
    exit 1
fi

# Source the environment variables
source .env.local

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found in .env.local"
    echo "Please add your Neon database URL to .env.local"
    exit 1
fi

echo "📡 Connecting to Neon database..."

# Execute the schema
if psql "$DATABASE_URL" -f database_schema.sql; then
    echo "✅ Database schema executed successfully!"
    
    # Test the setup
    echo "🧪 Testing database setup..."
    
    if psql "$DATABASE_URL" -c "SELECT 'Database setup successful!' as status;"; then
        echo "🎉 Database setup completed successfully!"
        echo "🔗 Your Hintify database is ready for authentication and data storage."
    else
        echo "⚠️ Schema executed but test query failed"
    fi
else
    echo "❌ Failed to execute database schema"
    echo "Please check your database connection and schema file"
    exit 1
fi