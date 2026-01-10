-- =============================================================================
-- Dave Local Database Initialization (Simplified for Testing)
-- =============================================================================
-- Based on: Dave/supabase/migrations/20260109_initial_schema_v2.sql
-- Simplified for: Local Docker PostgreSQL (no Supabase auth required)
-- Purpose: Fast local testing without cloud dependencies
--
-- ⚠️  WARNING: LOCAL TESTING ONLY - NOT FOR PRODUCTION
-- =============================================================================
--
-- This file uses STUB AUTH FUNCTIONS for local development speed.
--
-- ✅ SAFE FOR:
--   - Unit tests (business logic)
--   - Integration tests (conversation flows, data integrity)
--   - Fast local iteration
--
-- ❌ NOT SUITABLE FOR:
--   - Auth edge case testing (JWT, role switching, multi-tenant)
--   - Production deployment
--   - Final pre-deployment validation
--
-- 📋 TESTING STRATEGY:
--   - Phase 1-3: Use local DB (this file) for fast iteration
--   - Phase 4: MANDATORY cloud DB integration tests before deployment
--   - Mark auth-sensitive tests with @pytest.mark.integration_auth
--
-- 🔄 PRODUCTION MIGRATION:
--   - Production uses: Dave/supabase/migrations/20260109_initial_schema_v2.sql
--   - Cloud Dave DB: Real Supabase auth (auth.uid(), JWT tokens)
--   - Never deploy this local-init.sql to production
--
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- SIMPLIFIED AUTH STUB FUNCTIONS (For Local Testing Only)
-- =============================================================================
-- Note: These are no-op stubs that allow RLS policies to work locally
-- Real auth is handled by Supabase auth.uid() in production

CREATE SCHEMA IF NOT EXISTS auth;

-- Stub auth.uid() function that returns a test user UUID
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
    -- Return a consistent test user ID for local testing
    -- Tests can override this per session: SET auth.current_user_id = 'uuid';
    SELECT COALESCE(
        current_setting('auth.current_user_id', true)::uuid,
        '00000000-0000-0000-0000-000000000001'::uuid
    );
$$;

-- Stub is_admin_user() function
CREATE OR REPLACE FUNCTION is_admin_user()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    -- For local testing, check a session variable
    -- Tests can set: SET auth.is_admin = 'true';
    SELECT COALESCE(
        current_setting('auth.is_admin', true)::boolean,
        false
    );
$$;

COMMENT ON FUNCTION auth.uid() IS 'Local testing stub - returns test user UUID';
COMMENT ON FUNCTION is_admin_user() IS 'Local testing stub - checks session variable';

-- =============================================================================
-- TABLE: ai_conversations
-- =============================================================================
-- Stores conversation sessions between users and Dave AI
CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for ai_conversations
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_status ON ai_conversations(status);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_created_at ON ai_conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_context ON ai_conversations USING GIN (context);

COMMENT ON TABLE ai_conversations IS 'User conversation sessions with Dave AI';

-- =============================================================================
-- TABLE: ai_messages
-- =============================================================================
-- Stores individual messages within conversations
CREATE TABLE IF NOT EXISTS ai_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    resources TEXT[],
    follow_up_suggestions TEXT[]
);

-- Indexes for ai_messages
CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation_id ON ai_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_timestamp ON ai_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_messages_role ON ai_messages(role);
CREATE INDEX IF NOT EXISTS idx_ai_messages_metadata ON ai_messages USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_ai_messages_content_search ON ai_messages USING GIN (to_tsvector('english', content));

COMMENT ON TABLE ai_messages IS 'Individual messages within conversations';

-- =============================================================================
-- TABLE: admin_prompts
-- =============================================================================
-- Master table for Dave's system prompts
CREATE TABLE IF NOT EXISTS admin_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    current_version_id UUID,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(category, name)
);

CREATE INDEX IF NOT EXISTS idx_admin_prompts_category ON admin_prompts(category);
CREATE INDEX IF NOT EXISTS idx_admin_prompts_is_archived ON admin_prompts(is_archived);

COMMENT ON TABLE admin_prompts IS 'Dave system prompts (versioned)';

-- =============================================================================
-- TABLE: admin_prompt_versions
-- =============================================================================
-- Versioned content for each prompt
CREATE TABLE IF NOT EXISTS admin_prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES admin_prompts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    variables_schema JSONB,
    commit_message TEXT NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(prompt_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_admin_prompt_versions_prompt_id ON admin_prompt_versions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_admin_prompt_versions_created_at ON admin_prompt_versions(created_at DESC);

COMMENT ON TABLE admin_prompt_versions IS 'Version history for prompts';

-- =============================================================================
-- TABLE: admin_prompt_variables
-- =============================================================================
-- Reusable variables for prompt templates
CREATE TABLE IF NOT EXISTS admin_prompt_variables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    variable_name TEXT NOT NULL,
    variable_type TEXT NOT NULL CHECK (variable_type IN ('string', 'number', 'boolean', 'array', 'object')),
    description TEXT NOT NULL,
    example_value TEXT,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(category, variable_name)
);

CREATE INDEX IF NOT EXISTS idx_admin_prompt_variables_category ON admin_prompt_variables(category);

COMMENT ON TABLE admin_prompt_variables IS 'Reusable variables for prompt templates';

-- =============================================================================
-- ADD FOREIGN KEY for admin_prompts.current_version_id
-- =============================================================================
ALTER TABLE admin_prompts
    ADD CONSTRAINT fk_admin_prompts_current_version
    FOREIGN KEY (current_version_id)
    REFERENCES admin_prompt_versions(id)
    ON DELETE SET NULL;

-- =============================================================================
-- TRIGGERS: Auto-update updated_at timestamps
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ai_conversations_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_prompts_updated_at
    BEFORE UPDATE ON admin_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
-- Note: RLS is enabled but policies use stub auth functions for local testing
-- =============================================================================

-- Create stub roles for RLS (Supabase uses 'authenticated' and 'service_role')
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role;
    END IF;
END $$;

-- Grant permissions to postgres user to act as these roles
GRANT authenticated TO postgres;
GRANT service_role TO postgres;

-- Enable RLS on all tables
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_prompt_variables ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- TABLE 1: ai_conversations (User-Owned Resource)
-- =============================================================================

CREATE POLICY "select_own_ai_conversations"
    ON ai_conversations FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "insert_own_ai_conversations"
    ON ai_conversations FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "update_own_ai_conversations"
    ON ai_conversations FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "delete_own_ai_conversations"
    ON ai_conversations FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "service_role_ai_conversations"
    ON ai_conversations FOR ALL TO service_role
    USING (true);

GRANT SELECT, INSERT, UPDATE, DELETE ON ai_conversations TO authenticated;
GRANT ALL ON ai_conversations TO service_role;

-- =============================================================================
-- TABLE 2: ai_messages (Child Resource)
-- =============================================================================

CREATE POLICY "select_own_ai_messages"
    ON ai_messages FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM ai_conversations
            WHERE ai_conversations.id = ai_messages.conversation_id
              AND ai_conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "insert_own_ai_messages"
    ON ai_messages FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM ai_conversations
            WHERE ai_conversations.id = ai_messages.conversation_id
              AND ai_conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "update_own_ai_messages"
    ON ai_messages FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM ai_conversations
            WHERE ai_conversations.id = ai_messages.conversation_id
              AND ai_conversations.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM ai_conversations
            WHERE ai_conversations.id = ai_messages.conversation_id
              AND ai_conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "delete_own_ai_messages"
    ON ai_messages FOR DELETE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM ai_conversations
            WHERE ai_conversations.id = ai_messages.conversation_id
              AND ai_conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "service_role_ai_messages"
    ON ai_messages FOR ALL TO service_role
    USING (true);

GRANT SELECT, INSERT, UPDATE, DELETE ON ai_messages TO authenticated;
GRANT ALL ON ai_messages TO service_role;

-- =============================================================================
-- TABLE 3: admin_prompts (Public Read, Admin Write)
-- =============================================================================

CREATE POLICY "public_read_admin_prompts"
    ON admin_prompts FOR SELECT TO authenticated
    USING (is_archived = false);

CREATE POLICY "admin_manage_admin_prompts"
    ON admin_prompts FOR ALL TO authenticated
    USING (is_admin_user())
    WITH CHECK (is_admin_user());

CREATE POLICY "service_role_admin_prompts"
    ON admin_prompts FOR ALL TO service_role
    USING (true);

GRANT SELECT ON admin_prompts TO authenticated;
GRANT ALL ON admin_prompts TO service_role;

-- =============================================================================
-- TABLE 4: admin_prompt_versions (Public Read, Admin Write)
-- =============================================================================

CREATE POLICY "public_read_admin_prompt_versions"
    ON admin_prompt_versions FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "admin_manage_admin_prompt_versions"
    ON admin_prompt_versions FOR ALL TO authenticated
    USING (is_admin_user())
    WITH CHECK (is_admin_user());

CREATE POLICY "service_role_admin_prompt_versions"
    ON admin_prompt_versions FOR ALL TO service_role
    USING (true);

GRANT SELECT ON admin_prompt_versions TO authenticated;
GRANT ALL ON admin_prompt_versions TO service_role;

-- =============================================================================
-- TABLE 5: admin_prompt_variables (Public Read, Admin Write)
-- =============================================================================

CREATE POLICY "public_read_admin_prompt_variables"
    ON admin_prompt_variables FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "admin_manage_admin_prompt_variables"
    ON admin_prompt_variables FOR ALL TO authenticated
    USING (is_admin_user())
    WITH CHECK (is_admin_user());

CREATE POLICY "service_role_admin_prompt_variables"
    ON admin_prompt_variables FOR ALL TO service_role
    USING (true);

GRANT SELECT ON admin_prompt_variables TO authenticated;
GRANT ALL ON admin_prompt_variables TO service_role;

-- =============================================================================
-- GRANT USAGE ON SCHEMA
-- =============================================================================

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;
GRANT USAGE ON SCHEMA auth TO authenticated;
GRANT USAGE ON SCHEMA auth TO service_role;

-- =============================================================================
-- LOCAL TESTING HELPER: Set current user
-- =============================================================================

DO $$
BEGIN
    -- Set default test user for local development
    PERFORM set_config('auth.current_user_id', '00000000-0000-0000-0000-000000000001', false);
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Dave Local Database Initialized';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Created 5 tables with indexes and triggers';
    RAISE NOTICE '✓ Enabled RLS with simplified auth stubs';
    RAISE NOTICE '✓ Created stub roles: authenticated, service_role';
    RAISE NOTICE '✓ Set default test user: 00000000-0000-0000-0000-000000000001';
    RAISE NOTICE '';
    RAISE NOTICE 'Testing helpers:';
    RAISE NOTICE '  SET auth.current_user_id = ''your-uuid'';';
    RAISE NOTICE '  SET auth.is_admin = ''true'';';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for system prompts seed data';
END $$;
