-- Add last_fetched_at column to git_repositories for tracking fetch times
ALTER TABLE "git_repositories" ADD COLUMN "last_fetched_at" timestamp NULL;

-- Rename the contents table to contributions
ALTER TABLE "contents" RENAME TO "contributions";

-- Add the details column to store full GitHub API response data
ALTER TABLE "contributions" ADD COLUMN "details" jsonb NOT NULL DEFAULT '{}';

-- Update the foreign key constraint name to reflect the new table name
ALTER TABLE "contributions" DROP CONSTRAINT "repo_contents";
ALTER TABLE "contributions" ADD CONSTRAINT "repo_contributions" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");

-- Add index on the user, type, git_repository_id fkey, created_at and is_selected columns (1 index for each column)
CREATE INDEX "idx_contributions_user" ON "contributions" ("user");
CREATE INDEX "idx_contributions_type" ON "contributions" ("type");
CREATE INDEX "idx_contributions_repo" ON "contributions" ("git_repository_id");
CREATE INDEX "idx_contributions_created" ON "contributions" ("created_at");
CREATE INDEX "idx_contributions_selected" ON "contributions" ("is_selected");

-- Add index on last_fetched_at for efficient repository queries
CREATE INDEX "idx_git_repositories_last_fetched" ON "git_repositories" ("last_fetched_at");

-- Add comments to document the table and column purposes
COMMENT ON TABLE "contributions" IS 'Stores GitHub contribution data with full API response details';
COMMENT ON COLUMN "contributions"."details" IS 'Full GitHub API response data stored as JSONB';
COMMENT ON COLUMN "contributions"."type" IS 'Type of contribution: commit, pull_request, issue, release';
COMMENT ON COLUMN "contributions"."user" IS 'GitHub username of the contributor';
COMMENT ON COLUMN "contributions"."summary" IS 'Brief summary/description of the contribution';
COMMENT ON COLUMN "contributions"."is_selected" IS 'Whether this contribution is selected for processing';
COMMENT ON COLUMN "git_repositories"."last_fetched_at" IS 'Timestamp of the last successful contribution fetch for this repository';
