import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import ffmpeg

FEED_URL = "https://feedpress.me/rdvtech"
AUDIO_DIR = "data/audio"
RESULTS_FILE = "data/transcriptions.json"
EPISODES_TO_PROCESS = 4


def fetch_podcast_episodes():
    """Fetches and parses the podcast feed to extract episode info."""
    print(f"Fetching feed from {FEED_URL}...")
    try:
        response = requests.get(FEED_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching feed: {e}")
        return []

    # The feed is XML, so we use the lxml parser for reliability.
    soup = BeautifulSoup(response.content, "xml")
    episodes = []

    # In an RSS feed, episodes are inside <item> tags
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        date_tag = item.find("pubDate")
        date_obj = None
        if date_tag:
            # Format: Tue, 08 Jul 2025 07:00:00 GMT
            date_str = date_tag.get_text(strip=True)
            try:
                # We split and take all but the last part to remove the timezone
                date_str_no_tz = " ".join(date_str.split()[:-1])
                date_obj = datetime.strptime(date_str_no_tz, "%a, %d %b %Y %H:%M:%S")
            except (ValueError, IndexError) as e:
                print(f"Could not parse date: {date_str}, error: {e}")

        # The MP3 link is in an <enclosure> tag
        enclosure_tag = item.find("enclosure", type="audio/mpeg")
        mp3_url = None
        if enclosure_tag and enclosure_tag.has_attr("url"):
            mp3_url = enclosure_tag["url"]

        if title and mp3_url and date_obj:
            episodes.append(
                {
                    "title": title,
                    "url": mp3_url,
                    "date": date_obj,
                }
            )

    print(f"Found {len(episodes)} episodes.")
    return episodes


def download_audio(episode_title, url):
    """Downloads an audio file from a URL and saves it locally."""
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Créer un nom de fichier simple à partir du titre
    safe_filename = "".join(
        [c for c in episode_title if c.isalpha() or c.isdigit() or c == " "]
    ).rstrip()
    filepath = os.path.join(AUDIO_DIR, f"{safe_filename}.mp3")

    if os.path.exists(filepath):
        print(f"Audio for '{episode_title}' already downloaded.")
        return filepath

    print(f"Downloading audio for '{episode_title}'...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved to {filepath}")
        return filepath
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None


def transcribe_audio(filepath):
    """Transcribes an audio file using the OpenAI Whisper API, handling large files by chunking."""
    if not filepath:
        return None

    client = OpenAI()
    # OpenAI has a 25MB file size limit.
    limit_mb = 25
    limit_bytes = limit_mb * 1024 * 1024

    file_size = os.path.getsize(filepath)

    if file_size < limit_bytes:
        print(f"Transcribing {os.path.basename(filepath)} with OpenAI API...")
        try:
            with open(filepath, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )
            print("Transcription complete.")
            return transcription
        except Exception as e:
            print(f"Error during OpenAI transcription: {e}")
            return None

    # File is too large, so we chunk it using ffmpeg.
    print(f"File {os.path.basename(filepath)} is larger than {limit_mb}MB, chunking...")
    temp_files = []
    try:
        # Get audio duration to calculate chunks
        probe = ffmpeg.probe(filepath)
        duration = float(probe["format"]["duration"])

        # 10 minutes is a safe interval.
        chunk_duration_s = 10 * 60
        num_chunks = int(duration / chunk_duration_s) + 1

        full_transcription = ""
        previous_transcription = ""

        for i in range(num_chunks):
            start_time = i * chunk_duration_s
            chunk_filepath = f"{os.path.splitext(filepath)[0]}_chunk_{i}.mp3"
            temp_files.append(chunk_filepath)
            print(f"Exporting and transcribing chunk {i+1}/{num_chunks}...")

            (
                ffmpeg.input(filepath, ss=start_time, t=chunk_duration_s)
                .output(chunk_filepath, acodec="copy")
                .run(overwrite_output=True, quiet=True)
            )

            with open(chunk_filepath, "rb") as audio_file:
                # To preserve context, we prompt with the transcription of the previous chunk.
                transcription_part = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    prompt=previous_transcription,
                )
                full_transcription += transcription_part + " "
                previous_transcription = transcription_part
        print("Transcription of all chunks complete.")
        return full_transcription.strip()

    except Exception as e:
        print(f"An error occurred during chunking and transcription: {e}")
        return None
    finally:
        # Clean up temporary files
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
        if temp_files:
            print("Cleaned up temporary chunk files.")


def main():
    """Main function to run the scraping and transcription process."""
    load_dotenv()
    episodes = fetch_podcast_episodes()
    if not episodes:
        return

    # Load already processed episodes to avoid re-transcribing
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                processed_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Warning: Could not read or parse {RESULTS_FILE}. Starting fresh.")
            processed_data = []
    else:
        processed_data = []

    processed_titles = {e["title"] for e in processed_data}
    episodes_to_process = [e for e in episodes if e["title"] not in processed_titles]

    # Sort episodes to process by date, newest first
    episodes_to_process.sort(key=lambda x: x["date"], reverse=True)

    print(f"Found {len(episodes_to_process)} new episodes to process.")

    newly_processed_data = []
    for episode in episodes_to_process[:EPISODES_TO_PROCESS]:
        title = episode["title"]
        url = episode["url"]

        audio_path = download_audio(title, url)
        if not audio_path:
            continue

        transcription = transcribe_audio(audio_path)
        if transcription:
            new_data_item = {
                "title": title,
                "date": episode["date"].isoformat(),
                "audio_url": url,
                "transcription": transcription,
            }
            processed_data.append(new_data_item)
            newly_processed_data.append(new_data_item)

    # Sauvegarder les résultats dans un fichier JSON
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(
        f"\nProcessed {len(newly_processed_data)} new episodes. "
        f"Total results in {RESULTS_FILE}: {len(processed_data)}"
    )
    if newly_processed_data:
        print("\n--- Example Transcription ---")
        print(f"Title: {newly_processed_data[0]['title']}")
        print(f"Date: {newly_processed_data[0]['date']}")
        print(f"Transcription (excerpt): {newly_processed_data[0]['transcription'][:300]}...")


if __name__ == "__main__":
    main()
