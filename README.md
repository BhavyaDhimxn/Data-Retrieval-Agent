# Finance Agent — Data Retrieval Assistant

A lightweight Retrieval-Augmented Generation (RAG) service that answers questions strictly from your PDF knowledge base. It exposes a Flask API for queries and uploads, builds/maintains a Chroma vector store, and optionally integrates with Slack.

## Features
- PDF ingestion via API upload
- Chunking and embeddings with `langchain` + `ChromaDB`
- Similarity search with score threshold; citations returned with answers
- Configurable chunking, ranking, and rate limiting
- Redis-backed rate limiting with automatic in-memory fallback
- Optional Slack bot using Socket Mode

## Architecture
- `api.py`: Flask app exposing `/ask` and `/knowledge_base`
- `vector_store.py`: PDF processing + Chroma vector store management
- `llm.py`: LLM client (Ollama `llama3`) + prompt template
- `config.py`: Paths, rate limits, chunking, search parameters
- `app.py`: Entry point to initialize vector store and run the Flask API
- `slack.py`: Optional Slack bot integration (separate entrypoint)

### Data flow
1. PDFs are placed in `knowledge_base/` or uploaded via `/knowledge_base`.
2. `vector_store.py` splits, embeds, and persists to `db/` (Chroma).
3. `/ask` retrieves top chunks by similarity and feeds them to the LLM with a strict context-bound prompt.
4. Response includes the answer and citations.

## Prerequisites
- Python 3.10+
- Optional: Redis (for production-grade rate limiting). Without Redis, in-memory storage is used.
- Ollama installed locally with the `llama3` model pulled:
  ```bash
  brew install ollama || curl -fsSL https://ollama.com/install.sh | sh
  ollama pull llama3
  ollama serve  # ensure it's running
  ```

## Installation
```bash
# From project root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Set environment variables as needed (place in `.env` or export in shell):
- `SLACK_BOT_TOKEN` (Slack bot token)
- `SLACK_SIGNING_SECRET` (Slack signing secret)
- `SLACK_APP_TOKEN` (Slack app-level token for Socket Mode)

Defaults and paths are defined in `config.py`:
- `FOLDER_PATH = "db"` (Chroma persistence)
- `KNOWLEDGE_BASE_PATH = "knowledge_base"`
- `PROCESSED_FILES_PATH = "knowledge_base/processed_files.txt"`
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `SEARCH_K`, `SCORE_THRESHOLD`
- `RATE_LIMIT = "10/minute"`

## Running the API
1. Ensure Ollama is running and the `llama3` model is available.
2. Start the service:
   ```bash
   python app.py
   ```
   - On startup, the vector store is initialized and any new PDFs are processed.
   - The API serves on `http://localhost:5000`.

### Endpoints
- `POST /ask`
  - Request JSON: `{ "query": "Your question" }`
  - Response JSON: `{ "answer": str, "sources": [{"source": str, "page": int|"N/A"}] }`
  - Example:
    ```bash
    curl -s -X POST http://localhost:5000/ask \
      -H 'Content-Type: application/json' \
      -d '{"query":"What are the tax changes for 2024?"}' | jq
    ```

- `POST /knowledge_base` (upload a PDF)
  - Multipart form-data with file field `file`
  - Response includes processing status and chunk count
  - Example:
    ```bash
    curl -s -X POST http://localhost:5000/knowledge_base \
      -F file=@knowledge_base/2024.pdf | jq
    ```

## Optional: Slack Bot
`slack.py` provides a Socket Mode Slack bot that replies in-channel using the same retriever and LLM prompt.

Important notes:
- `vector_store.py` no longer initializes on import. Ensure it is initialized before Slack handles messages. Easiest path is to run `python app.py` once to build the index, or initialize programmatically.
- Required env vars: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`.

Run the bot (after the vector store has been initialized by the API):
```bash
python -c "from vector_store import initialize_vector_store; initialize_vector_store(); from slack import start_slack_bot; start_slack_bot()"
```

## Repository hygiene
This repo is configured to avoid committing large or generated files:
- `.gitignore` excludes:
  - Virtualenvs (`.venv/`, `slackbot-env/`)
  - Compiled caches (`__pycache__/`, `*.pyc`)
  - Local DB and artifacts (`db/`, `chroma.sqlite3`)
  - Knowledge base PDFs and state file (`knowledge_base/*.pdf`, `knowledge_base/processed_files.txt`)
  - OS/IDE files (`.DS_Store`, `.vscode/`, `.idea/`)

If you previously committed large files and GitHub rejects your push, purge them from history:
```bash
pip install git-filter-repo
# Remove data and PDFs from history
git filter-repo --force --path db --path knowledge_base --invert-paths
git push --force origin main
```

## Troubleshooting
- Redis not installed or running
  - The API will automatically use `memory://` storage for rate limiting. For production, run Redis and restart.
- Ollama not running / model missing
  - Ensure `ollama serve` is up and `ollama pull llama3` has been executed.
- Import or version errors for LangChain/Chroma
  - Reinstall: `pip install -r requirements.txt` and ensure consistent `langchain`, `langchain-community`, `langchain-chroma`, and `chromadb` versions.
- Uploads not processed
  - Confirm files land in `knowledge_base/`. Check logs for chunk counts after upload.
- Slack bot not responding
  - Confirm env vars are set, Socket Mode is enabled, App-level token is correct, and the vector store has been initialized.

## Project structure
```
app.py                 # Entry point: initialize vector store + run API
api.py                 # Flask API: /ask, /knowledge_base
vector_store.py        # PDF processing + Chroma vector store
llm.py                 # Ollama LLM and prompt template
config.py              # Settings (paths, chunking, search, rate limits)
slack.py               # Optional Slack bot (Socket Mode)
knowledge_base/        # PDFs (ignored in Git)
db/                    # Vector store persistence (ignored in Git)
```


