# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NotPatrick is a podcast analysis system that scrapes, transcribes, embeds, and enables querying of podcast episodes from the "RDV Tech" podcast feed. The system consists of three main modules that form a complete RAG (Retrieval-Augmented Generation) pipeline.

## Architecture

The codebase is organized into three core modules under `src/`:

1. **Audio Scraping (`audio_scrap/`)**: Downloads podcast episodes from RSS feeds and transcribes them using OpenAI Whisper
2. **Embedding (`embed/`)**: Chunks transcriptions and stores embeddings in Pinecone vector database  
3. **Query (`query/`)**: RAG-based chat interface using LlamaIndex for querying podcast content

### Data Flow
1. `audio_scrap` fetches podcast RSS → downloads MP3s → transcribes to text → saves to `data/transcriptions.json`
2. `embed` reads transcriptions → chunks text → generates embeddings → stores in Pinecone
3. `query` uses LlamaIndex + Pinecone for conversational podcast search with chat memory

## Development Commands

### Linting
```bash
uv run ruff check
```

### Running Modules
```bash
# Scrape and transcribe podcast episodes
uv run -m audio_scrap.main

# Generate and store embeddings
uv run -m embed.main

# Start interactive query chat interface
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
- **Custom Postprocessor**: `MetadataPrefixPostProcessor` prepends episode dates to retrieved chunks for better context (src/query/prefix.py)
- **Chat Engine**: Uses CondensePlusContextChatEngine with Cohere reranking and 3000-token memory buffer (src/query/main.py:75-85)

## Data Storage

- `data/audio/`: Downloaded MP3 files
- `data/transcriptions.json`: Episode transcriptions with metadata
- Pinecone index: "notpatrick" (serverless, AWS us-east-1)
