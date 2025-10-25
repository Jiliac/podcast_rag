#!/usr/bin/env python3
"""
Standalone script to transcribe audio from a URL.

Usage:
    uv run python scripts/transcribe_url.py <audio_url> [output_file]

Examples:
    uv run python scripts/transcribe_url.py https://example.com/podcast.mp3
    uv run python scripts/transcribe_url.py https://example.com/podcast.mp3 transcript.txt
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
from src.audio_scrap.main import download_audio, transcribe_audio


def transcribe_from_url(url: str, output_file: str = None) -> str:
    """
    Download audio from URL and transcribe it.

    Args:
        url: URL to the audio file
        output_file: Optional path to save the transcript. If None, prints to stdout.

    Returns:
        The transcription text
    """
    load_dotenv()
    client = OpenAI()

    # Use the URL as a simple title for the downloaded file
    # Extract filename from URL or use a generic name
    title = url.split("/")[-1].split("?")[0].replace(".mp3", "")
    if not title:
        title = "audio_file"

    print(f"Downloading audio from {url}...", file=sys.stderr)
    audio_path = download_audio(title, url)

    if not audio_path:
        print("Error: Failed to download audio file.", file=sys.stderr)
        sys.exit(1)

    print(f"Transcribing audio...", file=sys.stderr)
    transcript = transcribe_audio(client, audio_path)

    if not transcript:
        print("Error: Failed to transcribe audio.", file=sys.stderr)
        sys.exit(1)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        print(f"Transcript saved to {output_file}", file=sys.stderr)
    else:
        print("\n--- TRANSCRIPT ---", file=sys.stderr)
        print(transcript)

    return transcript


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    transcribe_from_url(url, output_file)


if __name__ == "__main__":
    main()
