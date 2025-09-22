-- Hintify Database Schema
-- This script sets up the complete database schema for the Hintify app

-- Create app_data schema for storing Hintify app data
CREATE SCHEMA IF NOT EXISTS app_data;

-- Create users table to store user information
CREATE TABLE IF NOT EXISTS app_data.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stack_user_id VARCHAR(255) UNIQUE,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  first_name VARCHAR(255),
  last_name VARCHAR(255),
  username VARCHAR(255),
  image_url TEXT,
  provider VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT true
);

-- Create app_sessions table to track user sessions
CREATE TABLE IF NOT EXISTS app_data.app_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES app_data.users(id) ON DELETE CASCADE,
  session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  session_end TIMESTAMP WITH TIME ZONE,
  device_info JSONB,
  app_version VARCHAR(50),
  is_active BOOLEAN DEFAULT true
);

-- Create questions table to store user questions
CREATE TABLE IF NOT EXISTS app_data.questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES app_data.users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES app_data.app_sessions(id) ON DELETE SET NULL,
  question_text TEXT NOT NULL,
  question_type VARCHAR(100), -- 'text', 'image', 'ocr', etc.
  image_data TEXT, -- base64 or url for images
  metadata JSONB, -- additional question metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create answers table to store AI responses
CREATE TABLE IF NOT EXISTS app_data.answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES app_data.questions(id) ON DELETE CASCADE,
  user_id UUID REFERENCES app_data.users(id) ON DELETE CASCADE,
  answer_text TEXT NOT NULL,
  ai_provider VARCHAR(100), -- 'gemini', 'ollama', etc.
  ai_model VARCHAR(100),
  confidence_score DECIMAL(3,2),
  processing_time_ms INTEGER,
  feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
  feedback_comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create app_usage table to track feature usage
CREATE TABLE IF NOT EXISTS app_data.app_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES app_data.users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES app_data.app_sessions(id) ON DELETE SET NULL,
  feature_name VARCHAR(255) NOT NULL, -- 'screenshot', 'clipboard', 'settings', etc.
  action VARCHAR(100) NOT NULL, -- 'capture', 'process', 'view', 'update', etc.
  details JSONB, -- additional usage details
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create data_transfers table to track data exports to Portal
CREATE TABLE IF NOT EXISTS app_data.data_transfers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES app_data.users(id) ON DELETE CASCADE,
  transfer_type VARCHAR(100) NOT NULL, -- 'questions', 'answers', 'usage', 'full_export'
  status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
  data_snapshot JSONB, -- snapshot of transferred data
  transfer_url TEXT, -- URL to Portal or export location
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_stack_user_id ON app_data.users(stack_user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON app_data.users(email);
CREATE INDEX IF NOT EXISTS idx_questions_user_id ON app_data.questions(user_id);
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON app_data.questions(created_at);
CREATE INDEX IF NOT EXISTS idx_answers_question_id ON app_data.answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_user_id ON app_data.answers(user_id);
CREATE INDEX IF NOT EXISTS idx_app_usage_user_id ON app_data.app_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_app_usage_timestamp ON app_data.app_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_data_transfers_user_id ON app_data.data_transfers(user_id);
CREATE INDEX IF NOT EXISTS idx_app_sessions_user_id ON app_data.app_sessions(user_id);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION app_data.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to users table
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON app_data.users 
    FOR EACH ROW 
    EXECUTE FUNCTION app_data.update_updated_at_column();

-- Create helper functions for data operations
CREATE OR REPLACE FUNCTION app_data.create_or_update_user(
    p_stack_user_id VARCHAR(255),
    p_email VARCHAR(255),
    p_name VARCHAR(255) DEFAULT NULL,
    p_first_name VARCHAR(255) DEFAULT NULL,
    p_last_name VARCHAR(255) DEFAULT NULL,
    p_username VARCHAR(255) DEFAULT NULL,
    p_image_url TEXT DEFAULT NULL,
    p_provider VARCHAR(100) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    user_id UUID;
BEGIN
    INSERT INTO app_data.users (
        stack_user_id, email, name, first_name, last_name, 
        username, image_url, provider, last_login
    ) VALUES (
        p_stack_user_id, p_email, p_name, p_first_name, p_last_name,
        p_username, p_image_url, p_provider, CURRENT_TIMESTAMP
    )
    ON CONFLICT (email) 
    DO UPDATE SET
        stack_user_id = EXCLUDED.stack_user_id,
        name = COALESCE(EXCLUDED.name, app_data.users.name),
        first_name = COALESCE(EXCLUDED.first_name, app_data.users.first_name),
        last_name = COALESCE(EXCLUDED.last_name, app_data.users.last_name),
        username = COALESCE(EXCLUDED.username, app_data.users.username),
        image_url = COALESCE(EXCLUDED.image_url, app_data.users.image_url),
        provider = COALESCE(EXCLUDED.provider, app_data.users.provider),
        last_login = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO user_id;
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to start a new app session
CREATE OR REPLACE FUNCTION app_data.start_app_session(
    p_user_id UUID,
    p_device_info JSONB DEFAULT NULL,
    p_app_version VARCHAR(50) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    session_id UUID;
BEGIN
    -- End any existing active sessions for this user
    UPDATE app_data.app_sessions 
    SET is_active = false, session_end = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id AND is_active = true;
    
    -- Create new session
    INSERT INTO app_data.app_sessions (user_id, device_info, app_version)
    VALUES (p_user_id, p_device_info, p_app_version)
    RETURNING id INTO session_id;
    
    RETURN session_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to log app usage
CREATE OR REPLACE FUNCTION app_data.log_usage(
    p_user_id UUID,
    p_session_id UUID,
    p_feature_name VARCHAR(255),
    p_action VARCHAR(100),
    p_details JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    usage_id UUID;
BEGIN
    INSERT INTO app_data.app_usage (user_id, session_id, feature_name, action, details)
    VALUES (p_user_id, p_session_id, p_feature_name, p_action, p_details)
    RETURNING id INTO usage_id;
    
    RETURN usage_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user summary data for Portal transfer
CREATE OR REPLACE FUNCTION app_data.get_user_data_summary(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'user_info', (
            SELECT jsonb_build_object(
                'id', id,
                'email', email,
                'name', name,
                'created_at', created_at,
                'last_login', last_login
            )
            FROM app_data.users 
            WHERE id = p_user_id
        ),
        'stats', jsonb_build_object(
            'total_questions', (
                SELECT COUNT(*) FROM app_data.questions WHERE user_id = p_user_id
            ),
            'total_answers', (
                SELECT COUNT(*) FROM app_data.answers WHERE user_id = p_user_id
            ),
            'total_sessions', (
                SELECT COUNT(*) FROM app_data.app_sessions WHERE user_id = p_user_id
            ),
            'app_usage_events', (
                SELECT COUNT(*) FROM app_data.app_usage WHERE user_id = p_user_id
            )
        ),
        'recent_activity', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'question', q.question_text,
                    'answer', a.answer_text,
                    'created_at', q.created_at,
                    'ai_provider', a.ai_provider
                )
            )
            FROM app_data.questions q
            LEFT JOIN app_data.answers a ON q.id = a.question_id
            WHERE q.user_id = p_user_id
            ORDER BY q.created_at DESC
            LIMIT 10
        )
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;