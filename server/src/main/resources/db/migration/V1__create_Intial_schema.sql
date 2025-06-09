CREATE TABLE "git_repositories" (
                                    "id" bigint PRIMARY KEY NOT NULL,
                                    "repository_link" text UNIQUE NOT NULL,
                                    "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE "personal_access_tokens" (
                                          "pat" text PRIMARY KEY NOT NULL,
                                          "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE "summaries" (
                             "id" bigint PRIMARY KEY NOT NULL,
                             "git_repository_id" bigint NOT NULL,
                             "summary" text NOT NULL,
                             "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "contents" (
                            "id" text PRIMARY KEY NOT NULL,
                            "git_repository_id" bigint NOT NULL,
                            "type" text NOT NULL,
                            "user" text NOT NULL,
                            "summary" text NOT NULL,
                            "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE "questions" (
                             "id" bigint PRIMARY KEY NOT NULL,
                             "git_repository_id" bigint NOT NULL,
                             "question" text NOT NULL,
                             "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE "question_answers" (
                                    "id" bigint PRIMARY KEY NOT NULL,
                                    "question_id" bigint NOT NULL,
                                    "answer" text NOT NULL,
                                    "created_at" timestamp NOT NULL DEFAULT (now())
);

CREATE TABLE "links" (
                         "id" uuid PRIMARY KEY NOT NULL,
                         "is_maintainer" bool NOT NULL,
                         "git_repository_id" bigint NOT NULL
);

CREATE TABLE "personal_access_tokens_git_repositories" (
                                                           "personal_access_tokens_pat" text,
                                                           "git_repositories_id" bigint,
                                                           PRIMARY KEY ("personal_access_tokens_pat", "git_repositories_id")
);

ALTER TABLE "personal_access_tokens_git_repositories" ADD FOREIGN KEY ("personal_access_tokens_pat") REFERENCES "personal_access_tokens" ("pat");

ALTER TABLE "personal_access_tokens_git_repositories" ADD FOREIGN KEY ("git_repositories_id") REFERENCES "git_repositories" ("id");


ALTER TABLE "summaries" ADD CONSTRAINT "repo_summaries" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");

ALTER TABLE "contents" ADD CONSTRAINT "repo_contents" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");

ALTER TABLE "questions" ADD CONSTRAINT "repo_questions" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");

ALTER TABLE "question_answers" ADD CONSTRAINT "repo_question" FOREIGN KEY ("question_id") REFERENCES "questions" ("id");

ALTER TABLE "links" ADD CONSTRAINT "repo_links" FOREIGN KEY ("git_repository_id") REFERENCES "git_repositories" ("id");
