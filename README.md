# NotPatrick RAG MCP Server

This project provides a Retrieval-Augmented Generation (RAG) system for the "Not Patrick" podcast. It scrapes episodes, transcribes them, creates embeddings, and exposes the RAG pipeline as a set of tools through a [FastMCP](https://github.com/viam-labs/fastmcp) server.

This allows AI agents and other clients to query the podcast's content in natural language.

## Features

- **Podcast Scraping**: Fetches the latest podcast episodes from the RSS feed.
- **Audio Transcription**: Downloads audio and transcribes it using OpenAI Whisper, with support for chunking large files.
- **Semantic Chunking & Embedding**: Chunks transcriptions semantically and generates vector embeddings using OpenAI models.
- **Vector Storage**: Stores and indexes embeddings in a Pinecone serverless index for efficient retrieval.
- **RAG Chat Engine**: Uses LlamaIndex and Cohere Rerank to provide accurate, context-aware answers from podcast content.
- **MCP Tool Server**: Exposes functionality via a `FastMCP` server, including:
  - `query_podcast`: Ask questions about the podcast.
  - `get_episode_info`: Retrieve metadata for a specific episode by date.
  - `list_episodes`: List episodes within a date range.
- **Authentication**: Secures the server-client connection using JWT (JWS) with RSA key pairs.
- **Deployment-Ready**: Includes configuration for deploying with Docker and Fly.io.

## Prerequisites

- **Python 3.13+** and `uv`
- **`ffmpeg`**: Required for audio processing.
  - On macOS: `brew install ffmpeg`
  - On Debian/Ubuntu: `sudo apt-get install ffmpeg`
- **API Keys**:
  - OpenAI
  - Pinecone
  - Cohere

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/notpatrick-rag-mcp.git
    cd notpatrick-rag-mcp
    ```

2.  **Install Python dependencies:**
    ```bash
    uv sync
    ```

3.  **Set up environment variables:**
    Create a `.env` file by copying the example and add your API keys.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and fill in your keys:
    ```
    OPENAI_API_KEY="sk-..."
    PINECONE_API_KEY="..."
    COHERE_API_KEY="..."
    ```

4.  **Generate Authentication Keys:**
    The server uses a public/private key pair to authenticate the client. Generate them from the project root:
    ```bash
    uv run python scripts/generate_keys.py
    ```
    This creates `public_key.pem` (used by the server) and `private_key.pem`. Follow the instructions printed by the script to copy the private key to the client directory.

## Data Pipeline: Indexing Episodes

Before running the server, you need to populate the Pinecone index with the podcast data.

1.  **Step 1: Scrape and Transcribe Episodes**
    This script fetches the latest episodes from the RSS feed, downloads the audio, and transcribes it using Whisper. The results are saved to `data/transcriptions.json`.
    ```bash
    uv run -m audio_scrap.main
    ```
    *Note: By default, this processes the 4 latest episodes. You can change `EPISODES_TO_PROCESS` in `src/audio_scrap/main.py` to process more.*

2.  **Step 2: Embed and Index Content**
    This script chunks the transcriptions, generates embeddings for each chunk, and uploads them to your Pinecone index.
    ```bash
    uv run -m embed.main
    ```
    The script will create the Pinecone index if it doesn't exist and skips episodes that are already indexed.

## Running the Server

Once the data pipeline is complete, you can start the MCP server.

```bash
uv run -m rag_mcp.main
```

The server will be available at `http://localhost:8000`. It exposes the tools over a Server-Sent Events (SSE) endpoint, typically at `http://localhost:8000/sse`.

## Running the Test Client

A TypeScript-based client is available in the `mcp-client/` directory to test the server's functionality. It demonstrates how to connect to the server, discover tools, and use them with the Vercel AI SDK.

For instructions, see the client's README:
[mcp-client/README.md](mcp-client/README.md)

## Deployment

### Docker

The project includes a `Dockerfile` and `docker-compose.yml` for containerized deployment.

To build and run the service with Docker Compose:
```bash
# Ensure your .env file is populated
docker-compose up --build
```

### Fly.io

The `fly.toml` file is configured for easy deployment to [Fly.io](https://fly.io/). After installing the `flyctl` CLI and signing in, you can deploy the application:

1.  **Create an app:**
    ```bash
    fly app create notpatrick-rag-mcp
    ```

2.  **Set secrets:**
    Your API keys must be set as secrets in Fly.io.
    ```bash
    fly secrets set OPENAI_API_KEY="sk-..." PINECONE_API_KEY="..." COHERE_API_KEY="..."
    ```

3.  **Deploy:**
    ```bash
    fly deploy
    ```
    
*Note on Authentication*: For JWT authentication to work on the deployed server, the `public_key.pem` file must be copied into the Docker image. This is handled by the `Dockerfile`. Without it, the server will start without authentication enabled.
