-- V6__add_full_summary_to_summaries.sql

ALTER TABLE "summaries" RENAME COLUMN "summary" TO "overview";
ALTER TABLE "summaries" ADD COLUMN "commits_summary" TEXT;
ALTER TABLE "summaries" ADD COLUMN "pull_requests_summary" TEXT;
ALTER TABLE "summaries" ADD COLUMN "issues_summary" TEXT;
ALTER TABLE "summaries" ADD COLUMN "releases_summary" TEXT;
ALTER TABLE "summaries" ADD COLUMN "analysis" TEXT;
ALTER TABLE "summaries" ADD COLUMN "key_achievements" TEXT[];
ALTER TABLE "summaries" ADD COLUMN "areas_for_improvement" TEXT[];
ALTER TABLE "summaries" ADD COLUMN "total_contributions" INTEGER;
ALTER TABLE "summaries" ADD COLUMN "commits_count" INTEGER;
ALTER TABLE "summaries" ADD COLUMN "pull_requests_count" INTEGER;
ALTER TABLE "summaries" ADD COLUMN "issues_count" INTEGER;
ALTER TABLE "summaries" ADD COLUMN "releases_count" INTEGER;
