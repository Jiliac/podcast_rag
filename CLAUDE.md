# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NotPatrick is a podcast analysis system that scrapes, transcribes, embeds, and enables querying of podcast episodes from the "RDV Tech" podcast feed. The system has evolved into an MCP (Model Context Protocol) based architecture that exposes podcast querying capabilities as tools for AI assistants and applications.

## Architecture

The system consists of the following components:

### Core Processing Modules (`src/`)
1. **Audio Scraping (`audio_scrap/`)**: Downloads podcast episodes from RSS feeds and transcribes them using OpenAI Whisper
2. **Embedding (`embed/`)**: Chunks transcriptions and stores embeddings in Pinecone vector database  
3. **Query (`query/`)**: RAG-based chat interface using LlamaIndex for querying podcast content (legacy interface)

### MCP (Model Context Protocol) Components
4. **RAG MCP Server (`rag_mcp/`)**: FastMCP server that exposes podcast querying as an MCP tool with JWT authentication
5. **MCP Client (`mcp-client/`)**: TypeScript client demonstrating integration with AI SDK for testing and development

### Data Flow
1. **Data Pipeline**: `audio_scrap` → `embed` → Pinecone vector store
2. **MCP Service**: `rag_mcp` server exposes `query_podcast` tool over HTTP/SSE
3. **Client Integration**: Applications connect via MCP protocol to query podcast content using AI assistants

## Development Commands

### Linting
```bash
uv run ruff check
```

### Data Processing
```bash
# Scrape and transcribe podcast episodes
uv run -m audio_scrap.main

# Generate and store embeddings
uv run -m embed.main
```

### MCP Server & Client
```bash
# Start the MCP server (primary interface)
uv run -m rag_mcp.main

# Generate authentication keys (run once)
uv run python scripts/generate_keys.py

# Test with TypeScript MCP client
cd mcp-client
pnpm install
pnpm dev
```

### Legacy Interface
```bash
# Start interactive query chat interface (legacy)
uv run -m query.main
```

## Dependencies & Environment

The project uses `uv` for dependency management with Python 3.13+. Key dependencies include:
- OpenAI (Whisper transcription, embeddings, LLM)
- Pinecone (vector storage)
- LlamaIndex (RAG framework)
- Cohere (optional reranking)
- FFmpeg (audio chunking for large files)

Required environment variables:
- `OPENAI_API_KEY`
- `PINECONE_API_KEY` 
- `COHERE_API_KEY` (optional, for reranking)

## Key Implementation Details

- **Audio Processing**: Handles large audio files by chunking into 10-minute segments when > 25MB (src/audio_scrap/main.py:122-172)
- **Embedding Strategy**: Uses semantic chunking with text-embedding-3-large model, stores in Pinecone with episode metadata (src/embed/main.py)
- **Custom Postprocessor**: `MetadataPrefixPostProcessor` prepends episode dates to retrieved chunks for better context (src/rag_mcp/prefix.py)
- **MCP Authentication**: Uses JWT bearer tokens with RSA256 for secure server access (src/rag_mcp/main.py:28-42)
- **Stateless Design**: Each MCP query creates fresh chat engine instance for consistent responses (src/rag_mcp/main.py:112-130)
- **Chat Engine**: Uses CondensePlusContextChatEngine with Cohere reranking and 3000-token memory buffer

## Data Storage

- `data/audio/`: Downloaded MP3 files
- `data/transcriptions.json`: Episode transcriptions with metadata
- Pinecone index: "notpatrick" (serverless, AWS us-east-1)
