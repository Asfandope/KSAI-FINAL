-- Initialize KS AI Database
-- This script sets up the initial database schema and data

-- Enum types for consistency and validation
CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE content_type AS ENUM ('pdf', 'youtube');
CREATE TYPE content_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE language_code AS ENUM ('en', 'ta');
CREATE TYPE message_sender AS ENUM ('user', 'ai');

-- Users table to store authentication and role information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT email_or_phone_check CHECK (email IS NOT NULL OR phone_number IS NOT NULL)
);

-- Content table to store metadata about knowledge base items
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type content_type NOT NULL,
    language language_code NOT NULL,
    category VARCHAR(255) NOT NULL,
    needs_translation BOOLEAN NOT NULL DEFAULT FALSE,
    status content_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Conversations table to group chat sessions
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages table to store individual chat messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender message_sender NOT NULL,
    text_content TEXT NOT NULL,
    image_url TEXT,
    video_url TEXT,
    video_timestamp_seconds INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_content_category ON content(category);
CREATE INDEX idx_content_language ON content(language);

-- Function to automatically update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to call the function on update
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_content BEFORE UPDATE ON content FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_conversations BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- Insert default admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (email, password_hash, role) 
VALUES (
    'admin@ksai.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3cJDEWUOvS', 
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert sample content categories
INSERT INTO content (title, source_url, source_type, language, category, status) VALUES
    ('Sample Politics Document', 'sample-politics.pdf', 'pdf', 'en', 'Politics', 'completed'),
    ('Sample Environment Document', 'sample-environment.pdf', 'pdf', 'en', 'Environmentalism', 'completed'),
    ('Sample SKCRF Document', 'sample-skcrf.pdf', 'pdf', 'en', 'SKCRF', 'completed'),
    ('Sample Educational Trust Document', 'sample-education.pdf', 'pdf', 'en', 'Educational Trust', 'completed')
ON CONFLICT DO NOTHING;