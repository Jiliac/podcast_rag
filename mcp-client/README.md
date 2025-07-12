# MCP Client Test

A TypeScript client to test the NotPatrick MCP server using the AI SDK.

## Setup

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Create your environment file from the example at the project root:
   ```bash
   cp .env.example .env
   ```
   Edit the new `.env` file to add your API keys.

3. Generate and position the authentication key pair:
   ```bash
   # From the project root directory
   uv run python scripts/generate_keys.py
   
   # Copy the private key to the client directory
   cp private_key.pem mcp-client/private_key.pem
   ```
   This creates `public_key.pem` (for the server) and `private_key.pem`. Ensure you've copied the private key as shown above.

4. Make sure the NotPatrick MCP server is running:
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
