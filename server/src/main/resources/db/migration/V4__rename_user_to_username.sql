-- Rename user column to username to avoid PostgreSQL reserved keyword conflicts
ALTER TABLE contributions RENAME COLUMN "user" TO username; 