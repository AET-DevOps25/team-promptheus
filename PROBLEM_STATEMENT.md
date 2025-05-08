# Problem Statement for the DevOps Practical: Prompteus

## What is the main functionality?

As companies grow, answering the simple question “What’s happening right now?” becomes increasingly hard. Information is spread across tools, projects, and teams, making it difficult to get a clear, high-level view. 
Weekly status reports and ad‑hoc “What’s going on?” questions drain developer time and still leave managers digging through GitHub with its barely working search functionality and pretty labour-intensive project management.

Teams need a zero‑friction way to surface work done, highlight blockers, and answer follow‑up questions—all in one place, automatically.

## Who are the intended users?

- Developers — no more Friday write‑ups; focus on code.
- Managers — instant, trustworthy progress snapshots and interactive Q&A.
- Stakeholders — single GitHub Wiki page per week with concise, continuously appended insights.

## How will you integrate GenAI meaningfully?

- Completely hands‑off (GenAI generated) summaries of repository content yet
- Instant answers to (manager) questions without ping‑pong on Slack.
- Integrated AI-driven search via meilsearchs' vector embeddings allowing

## Some scenarios how our app will function

1. harvest (cron, daily to not exceed rate limit): pull all GitHub events —commits, PRs, reviews, issues, comments.
2. Vectorized context: index artifacts into Postgres pgvector for Retrieval‑Augmented Generation.
3. GenAI summarization: LangChain → LLM (OpenAI or local) outputs a Done / In‑Progress / Blocked / Next‑Week summary.
4. A frontend (React/Vue UI)
   - Shows the content from the database and allows selecting which of the items to include/exclude via checkboxes for summarization.
   - Questions can also be asked against the database content to build up an Q&A.
   - An AI-driven semantic search bar helps users find content by semantics, not just a typo tolerant prefix-based system. 
5. Auto‑publish: every Friday run appends the team’s Markdown summary (one‑click regenerate summary) + any approved Q&A to the rolling GitHub Wiki page.
6. Observability: Prometheus logs summary latency, Q&A response time, regeneration count, harvesting latency+status
7. Deployment: Zero‑touch delivery: CI/CD on GitHub Actions builds containers, deploys to docker compose/…
