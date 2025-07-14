import json
import os
import re
from uuid import uuid4

from chonkie import SemanticChunker
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Constants
TRANSCRIPTIONS_PATH = "data/transcriptions.json"
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072  # For text-embedding-3-large
PINECONE_INDEX_NAME = "notpatrick"
UPSERT_BATCH_SIZE = 100


def slugify(text: str) -> str:
    """Converts text to a URL-friendly slug valid for Pinecone namespaces."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text)
    return text.strip("-")


def setup_pinecone():
    """Initializes Pinecone and creates the index if it doesn't exist."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set.")

    pc = Pinecone(api_key=api_key)

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
        # Using serverless for cost-effectiveness, as it's usage-based.
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
        )
        print("Index created.")
    else:
        print(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists.")

    return pc.Index(PINECONE_INDEX_NAME)


def load_transcriptions():
    """Loads transcriptions from the JSON file."""
    if not os.path.exists(TRANSCRIPTIONS_PATH):
        print(f"Error: Transcriptions file not found at {TRANSCRIPTIONS_PATH}")
        return []
    try:
        with open(TRANSCRIPTIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {TRANSCRIPTIONS_PATH}")
        return []


def episode_already_embedded(index, title: str) -> bool:
    """
    Returns True if at least one vector already exists in Pinecone whose
    metadata.episode_title matches the given title. This uses a query with a
    metadata filter because `describe_index_stats` with a filter is not
    supported on serverless indexes.
    """
    try:
        # We query with a dummy vector because we only care about the metadata filter.
        # We set top_k=1 because we only need to know if at least one vector exists.
        query_result = index.query(
            vector=[0.0] * EMBEDDING_DIMENSION,
            filter={"episode_title": {"$eq": title}},
            top_k=1,
            include_values=False,
            include_metadata=False,
        )
        return len(query_result.get("matches", [])) > 0
    except Exception:
        # If the call fails, assume the episode is not yet embedded.
        return False


def main():
    """Main function to generate and store embeddings in Pinecone."""
    load_dotenv()
    index = setup_pinecone()

    transcriptions = load_transcriptions()
    if not transcriptions:
        return

    episodes_to_process = [
        e for e in transcriptions if not episode_already_embedded(index, e["title"])
    ]

    if not episodes_to_process:
        print("No new episodes to process. Pinecone is up to date.")
        return

    print(f"Found {len(episodes_to_process)} new episodes to process.")

    chunker = SemanticChunker()
    client = OpenAI()

    for episode in episodes_to_process:
        title = episode["title"]
        date = episode["date"]
        transcription = episode["transcription"]

        print(f"\nProcessing episode: '{title}'")

        if not transcription or not transcription.strip():
            print("  Skipping episode with empty transcription.")
            continue

        print("  Chunking transcription...")
        try:
            chunks = chunker.chunk(transcription)
            print(f"  Found {len(chunks)} chunks.")
        except Exception as e:
            print(f"  Error chunking transcription for '{title}': {e}")
            continue

        print("  Generating embeddings and preparing for upsert...")
        vectors_to_upsert = []
        for chunk in chunks:
            chunk_text = chunk.text
            try:
                # Generate embedding with OpenAI
                response = client.embeddings.create(
                    input=chunk_text, model=EMBEDDING_MODEL
                )
                embedding = response.data[0].embedding

                vector = {
                    "id": str(uuid4()),
                    "values": embedding,
                    "metadata": {
                        "episode_title": title,
                        "episode_date": date,
                        "chunk_text": chunk_text,
                    },
                }
                vectors_to_upsert.append(vector)
            except Exception as e:
                print(f"    Error processing chunk for '{title}': {e}")

        if not vectors_to_upsert:
            print(f"  No vectors generated for '{title}'. Skipping.")
            continue

        print(f"  Upserting {len(vectors_to_upsert)} vectors to Pinecone...")
        try:
            total_batches = (
                len(vectors_to_upsert) + UPSERT_BATCH_SIZE - 1
            ) // UPSERT_BATCH_SIZE
            for i in range(0, len(vectors_to_upsert), UPSERT_BATCH_SIZE):
                batch = vectors_to_upsert[i : i + UPSERT_BATCH_SIZE]
                print(
                    f"    Upserting batch {i//UPSERT_BATCH_SIZE + 1}/{total_batches}..."
                )
                index.upsert(vectors=batch)
            print(f"  Successfully processed and stored embeddings for '{title}'.")
        except Exception as e:
            print(f"  Error upserting vectors for '{title}': {e}")

    print("\nEmbedding process complete.")


if __name__ == "__main__":
    main()
