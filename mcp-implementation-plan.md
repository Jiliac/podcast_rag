# MCP Module Implementation Plan for NotPatrick RAG

## Overview
Create a new MCP module that exposes the NotPatrick RAG functionality through a FastMCP server for LibreChat integration.

## Implementation Steps

### 1. Add FastMCP Dependency
- Add fastmcp to pyproject.toml dependencies
- Update project to support the new MCP module

### 2. Create MCP Module Structure
```
src/
  mcp/
    __init__.py
    main.py      # FastMCP server implementation
```

### 3. Implement Basic FastMCP Server
- Create "hello world" MCP server in src/mcp/main.py
- Add a simple hello_world tool that returns a greeting
- Configure server to run on http://localhost:8000/mcp as expected by LibreChat
- Test integration with LibreChat to ensure MCP wiring works correctly

### 4. Extract RAG Logic
- Create rag.py to encapsulate the RAG setup logic from src/query/main.py
- Extract the chat engine initialization, Pinecone setup, and query processing
- Make it reusable for both CLI and MCP interfaces
- Add query_podcast tool to MCP server

### 5. Create Docker Configuration
- Create Dockerfile for containerizing the MCP server
- Create docker-compose.yml for easy deployment
- Ensure environment variables are properly configured
- Test containerized deployment

### 6. Update CLAUDE.md
- Document the new MCP module and how to run it
- Add commands: uv run -m mcp.main and Docker instructions
- Document LibreChat integration steps

## Key Features (Phase 1)
- Tool: hello_world() -> str - Simple greeting to test MCP integration

## Key Features (Phase 2)
- Tool: query_podcast(question: str) -> str - Query the podcast knowledge base
- Resource: Potentially expose available episodes/metadata

## Benefits
- Test MCP integration early with simple functionality
- Containerized deployment for easy LibreChat integration
- Incremental development approach
- Maintains separation between CLI and web interfaces

## Development Approach
1. Start with minimal MCP server to verify LibreChat integration
2. Incrementally add RAG functionality
3. Containerize for production deployment
4. Document for easy setup and maintenance