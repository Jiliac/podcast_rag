"""FastMCP server for NotPatrick RAG system."""

import os
from dotenv import load_dotenv

from pinecone import Pinecone

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional

from .prefix import MetadataPrefixPostProcessor
from .episode_info import get_episode_info_by_date, list_episodes_in_range

# Load environment variables
load_dotenv()

# Constants
PINECONE_INDEX_NAME = "notpatrick"
PUBLIC_KEY_PATH = "public_key.pem"

# Setup authentication provider
auth_provider = None
if os.path.exists(PUBLIC_KEY_PATH):
    print(f"INFO: Found '{PUBLIC_KEY_PATH}', enabling Bearer token authentication.")
    with open(PUBLIC_KEY_PATH, "r") as f:
        public_key = f.read()
    
    auth_provider = BearerAuthProvider(
        public_key=public_key,
        issuer="urn:notpatrick:client",
        audience="urn:notpatrick:server",
        algorithm="RS256"
    )
else:
    print(f"WARN: '{PUBLIC_KEY_PATH}' not found. Running without authentication.")

# Create the MCP server with authentication
mcp = FastMCP("NotPatrick RAG", auth=auth_provider)

# Global RAG components
index = None
node_postprocessors = None

def setup_pinecone_index():
    """Initializes Pinecone and returns the index object."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set.")
    
    pc = Pinecone(api_key=api_key)

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        raise ValueError(f"Pinecone index '{PINECONE_INDEX_NAME}' does not exist. Please run the embedding script first.")
    
    return pc.Index(PINECONE_INDEX_NAME)

def initialize_rag():
    """Initialize the RAG system."""
    global index, node_postprocessors
    
    # Configure core LlamaIndex settings
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    llm = OpenAI(model="gpt-4o")
    Settings.llm = llm

    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        print("Warning: COHERE_API_KEY not found. Reranking will be disabled.")
        cohere_rerank = None
    else:
        cohere_rerank = CohereRerank(api_key=cohere_api_key, top_n=3)

    # Initialize Pinecone
    pinecone_index = setup_pinecone_index()
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        text_key="chunk_text",
    )
    index = VectorStoreIndex.from_vector_store(vector_store)

    # Postprocessor to add metadata to the context
    metadata_postprocessor = MetadataPrefixPostProcessor(
        meta_key="episode_date"
    )

    # Setup node postprocessors - order matters!
    # 1. Rerank to get the most relevant nodes
    # 2. Add metadata to the text of the reranked nodes
    node_postprocessors = []
    if cohere_rerank:
        node_postprocessors.append(cohere_rerank)
    node_postprocessors.append(metadata_postprocessor)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "ok"})


@mcp.tool()
def query_podcast(question: str) -> str:
    """Query the Not Patrick podcast content using RAG.
    
    Args:
        question: The question to ask about the podcast content.
        
    Returns:
        An answer based on the podcast episodes.
    """
    print("CALLED query_podcast")
    if index is None or node_postprocessors is None:
        return "Error: RAG system not initialized. Please check server logs."
    
    try:
        # Create fresh memory and chat engine for each query (stateless)
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        # Setup chat engine with same configuration as query module
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=index.as_retriever(similarity_top_k=10),
            node_postprocessors=node_postprocessors,
            memory=memory,
            system_prompt="""Vous êtes un assistant conçu pour répondre aux questions sur le podcast 'Not Patrick'.
Utilisez les informations pertinentes des épisodes du podcast pour fournir une réponse complète et conversationnelle.
Chaque information est précédée de sa date d'épisode. Utilisez cette date pour contextualiser votre réponse.
Ne vous contentez pas de répéter le texte brut des sources.
Si vous ne trouvez pas d'information pertinente, indiquez que vous n'avez pas pu trouver l'information dans le podcast.
Soyez amical et engageant.""",
        )
        
        # Use chat instead of query for better conversational responses
        response = chat_engine.chat(question)
        return str(response)
    except Exception as e:
        return f"Error querying podcast: {str(e)}"


@mcp.tool()
def get_episode_info(date: str) -> str:
    """Get episode information by date.
    
    Args:
        date: Date string in various formats (YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.)
        
    Returns:
        JSON string with episode information (title, description, link, duration, etc.) or error message.
    """
    print("CALLED get_episode_info")
    try:
        episode_info = get_episode_info_by_date(date)
        
        if episode_info is None:
            return f"Error: No episode found for date '{date}'. Please check the date format (YYYY-MM-DD) and try again."
        
        # Format the response as a JSON string
        import json
        return json.dumps(episode_info, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error retrieving episode info: {str(e)}"


@mcp.tool()
def list_episodes(beginning: str = "", end: str = "") -> str:
    """List podcast episodes within a date range. The date range cannot exceed 12 months.
    If no dates are provided, it lists episodes from the last 3 months.
    
    Args:
        beginning: Start date (e.g., "YYYY-MM-DD"). If omitted or empty, defaults to 3 months ago.
        end: End date (e.g., "YYYY-MM-DD"). If omitted or empty, defaults to today.
        
    Returns:
        JSON string with a list of episodes, each containing 'episode_name' and 'date', sorted by date.
    """
    print("CALLED list_episodes")
    try:
        episodes = list_episodes_in_range(start_date_str=beginning, end_date_str=end)
        
        import json
        return json.dumps(episodes, indent=2, ensure_ascii=False)
        
    except ValueError as e:
        return f"Error listing episodes: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred while listing episodes: {str(e)}"


if __name__ == "__main__":
    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        initialize_rag()
        print("RAG system initialized successfully!")

        port = int(os.getenv("PORT", 8000))
        
        mcp.run(
            transport="sse",
            host="0.0.0.0",          # listen on all interfaces so it's reachable externally
            port=port,               # use the configured port
            log_level="info"         # optional
            # path="/mcp/"           # optional: change the SSE base path
        )
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
