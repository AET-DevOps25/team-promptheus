CREATE TABLE IF NOT EXISTS "repositories" (
  "id" uuid PRIMARY KEY NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "personal_access_tokens" (
  "id" integer PRIMARY KEY NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "summaries" (
  "id" integer PRIMARY KEY NOT NULL,
  "repository_id" integer NOT NULL,
  "summary" text NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "contents" (
  "id" integer PRIMARY KEY NOT NULL,
  "repository_id" integer NOT NULL,
  "type" text NOT NULL,
  "user" text NOT NULL,
  "summary" text NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "questions" (
  "id" integer PRIMARY KEY NOT NULL,
  "repository_id" integer NOT NULL,
  "question" text NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "question_answers" (
  "id" integer PRIMARY KEY NOT NULL,
  "question_id" integer NOT NULL,
  "answer" text NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "personal_access_tokens_repositories" (
  "personal_access_tokens_id" integer,
  "repositories_id" uuid,
  PRIMARY KEY ("personal_access_tokens_id", "repositories_id")
);

ALTER TABLE "personal_access_tokens_repositories" ADD FOREIGN KEY ("personal_access_tokens_id") REFERENCES "personal_access_tokens" ("id");

ALTER TABLE "personal_access_tokens_repositories" ADD FOREIGN KEY ("repositories_id") REFERENCES "repositories" ("id");


ALTER TABLE "summaries" ADD CONSTRAINT "repo_summaries" FOREIGN KEY ("repository_id") REFERENCES "repositories" ("id");

ALTER TABLE "contents" ADD CONSTRAINT "repo_contents" FOREIGN KEY ("repository_id") REFERENCES "repositories" ("id");

ALTER TABLE "questions" ADD CONSTRAINT "repo_questions" FOREIGN KEY ("repository_id") REFERENCES "repositories" ("id");

ALTER TABLE "question_answers" ADD CONSTRAINT "repo_question" FOREIGN KEY ("question_id") REFERENCES "questions" ("id");
