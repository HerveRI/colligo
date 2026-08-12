# COLLIGO
Self-hostable agentic RAG assistant that lets users ask natural-language questions over internal documents

## Stack
FastAPI - PostgreSQL/pgvector - React + Vite + Javascript - Ollama/hosted LLM APIs - Docker

## Setup
    uv sync
    cp .env.example .env

## Tests
    uv run pytest

## Lint
    uv run ruff check --fix .

## Notes
- EMBED_DIM must match the vector(N) column. Changing the embedding model requires a migration and re-embedding all rows.
- The chat model must support tool calling.
