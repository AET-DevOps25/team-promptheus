-- Extend existing summaries table for weekly summaries
ALTER TABLE summaries ADD COLUMN IF NOT EXISTS username text;
ALTER TABLE summaries ADD COLUMN IF NOT EXISTS week text;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_summaries_username ON summaries (username);
CREATE INDEX IF NOT EXISTS idx_summaries_week ON summaries (week);
CREATE UNIQUE INDEX IF NOT EXISTS idx_summaries_username_week ON summaries (username, week);
