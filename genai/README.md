# LangChain AI Service (Python / FastAPI)

This micro-service provides a simple REST API for interacting with OpenAI-powered chat models via LangChain.  It replaces the previous Node/Hono implementation.

---

## Endpoints

| Method | Path      | Description                     |
| ------ | --------- | --------------------------------|
| GET    | `/health` | Liveness probe ⇒ `{ "status": "ok" }` |
| POST   | `/predict`| Generate a completion. Body: `{ "input": "…" }` → `{ "output": "…" }` |

Interactive docs are served by FastAPI/Swagger at `/docs`.

---

## Running Locally

```bash
# (venv recommended)
cd genai
pip install -r requirements.txt
export OPENAI_API_KEY=sk-…
uvicorn app:app --reload --port 3003
```

Open <http://localhost:3003/docs> in your browser.

---

## Docker / Compose

```bash
docker compose build genai
docker compose up genai
```

The container image is built from `genai/Dockerfile` (Python 3.12-slim) and starts the service with `uvicorn`.

---

## Environment Variables

| Variable              | Default         | Description                         |
|-----------------------|-----------------|-------------------------------------|
| `GENAI_PORT`          | `3003`          | Port the service listens on         |
| `OPENAI_API_KEY`      | –               | Required. Your OpenAI API key       |
| `LANGCHAIN_MODEL_NAME`| `gpt-3.5-turbo` | Chat model to use                   |
| `LOG_LEVEL`           | `INFO`          | Python logging level                |

See `genai/env.example` for a template.

---

## Tests

```bash
pytest genai/tests -q
```

---

## Project Layout

```text
genai/
├── app.py            # FastAPI application
├── Dockerfile        # Runtime image
├── requirements.txt  # Python dependencies
├── tests/            # Pytest test-suite
└── …
```

Legacy Node/Hono files (e.g. `src/`, `package*.json`) have been kept only for reference; they are no longer used and can be safely deleted.
