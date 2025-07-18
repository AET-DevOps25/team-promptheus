-- Enhance question_answers table to store full GenAI response data
-- V9: Add JSONB support for rich question answer data

-- Add new columns for rich GenAI response data
ALTER TABLE question_answers
ADD COLUMN genai_question_id VARCHAR(36),  -- UUIDv7 from GenAI service
ADD COLUMN user_name VARCHAR(100),         -- Denormalized user for easy querying
ADD COLUMN week_id VARCHAR(10),            -- Denormalized week (e.g., 2025-W29)
ADD COLUMN question_text TEXT,             -- Denormalized question for easy access
ADD COLUMN full_response JSONB,            -- Complete GenAI response as JSONB
ADD COLUMN asked_at TIMESTAMP,             -- When question was asked (from GenAI)
ADD COLUMN response_time_ms INTEGER,       -- Response time from GenAI service
ADD COLUMN conversation_id VARCHAR(100);   -- Session ID for conversation context

-- Add indexes for common query patterns
CREATE INDEX idx_question_answers_genai_question_id ON question_answers(genai_question_id);
CREATE INDEX idx_question_answers_user_week ON question_answers(user_name, week_id);
CREATE INDEX idx_question_answers_asked_at ON question_answers(asked_at);
CREATE INDEX idx_question_answers_conversation_id ON question_answers(conversation_id);

-- Add GIN index for JSONB queries
CREATE INDEX idx_question_answers_full_response ON question_answers USING GIN(full_response);

-- Add comments for documentation
COMMENT ON COLUMN question_answers.genai_question_id IS 'UUIDv7 identifier from GenAI service response';
COMMENT ON COLUMN question_answers.user_name IS 'GitHub username - denormalized for performance';
COMMENT ON COLUMN question_answers.week_id IS 'ISO week format (YYYY-WXX) - denormalized for performance';
COMMENT ON COLUMN question_answers.question_text IS 'Question text - denormalized for easy access';
COMMENT ON COLUMN question_answers.full_response IS 'Complete GenAI response including evidence, reasoning steps, and suggested actions';
COMMENT ON COLUMN question_answers.asked_at IS 'Timestamp when question was processed by GenAI';
COMMENT ON COLUMN question_answers.response_time_ms IS 'GenAI service response time in milliseconds';
COMMENT ON COLUMN question_answers.conversation_id IS 'Session identifier for conversation context (user:week)';
