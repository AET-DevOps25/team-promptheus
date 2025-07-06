-- V7__update_contributions_composite_key.sql
-- Change contributions table to use composite primary key (type, id)

-- Drop the existing primary key constraint (inherited from the original "contents" table)
ALTER TABLE "contributions" DROP CONSTRAINT "contents_pkey";

-- Add the new composite primary key
ALTER TABLE "contributions" ADD CONSTRAINT "contributions_pkey" PRIMARY KEY ("type", "id");

-- Add comment to document the change
COMMENT ON CONSTRAINT "contributions_pkey" ON "contributions" IS 'Composite primary key ensures uniqueness across contribution types';
