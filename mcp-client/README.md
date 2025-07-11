# MCP Client Test

A TypeScript client to test the NotPatrick MCP server using the AI SDK.

## Setup

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Copy the environment file and add your OpenAI API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. Make sure the NotPatrick MCP server is running:
   ```bash
   # From the parent directory
   uv run -m rag_mcp.main
   ```

4. Run the client:
   ```bash
   pnpm dev
   ```

## What it does

This client:
- Connects to the MCP server running at `http://localhost:8000/mcp`
- Discovers available tools from the server
- Uses OpenAI GPT-4o-mini to call the `hello_world` tool
- Displays the results

The client demonstrates how to integrate MCP tools with the AI SDK for conversational AI applications.