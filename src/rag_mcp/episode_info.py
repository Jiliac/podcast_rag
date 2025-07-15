"""Episode information retrieval from RSS feed."""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

FEED_URL = "https://feedpress.me/rdvtech"


def fetch_podcast_episodes() -> List[Dict]:
    """Fetches and parses the podcast feed to extract episode info with rich metadata."""
    print(f"Fetching feed from {FEED_URL}...")
    try:
        response = requests.get(FEED_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching feed: {e}")
        return []

    # The feed is XML, so we use the xml parser for reliability.
    soup = BeautifulSoup(response.content, "xml")
    episodes = []

    # In an RSS feed, episodes are inside <item> tags
    for item in soup.find_all("item"):
        episode_data = {}
        
        # Title
        title_tag = item.find("title")
        if title_tag:
            episode_data["title"] = title_tag.get_text(strip=True)
        else:
            continue  # Skip episodes without titles

        # Date
        date_tag = item.find("pubDate")
        if date_tag:
            # Format: Tue, 08 Jul 2025 07:00:00 GMT
            date_str = date_tag.get_text(strip=True)
            try:
                # We split and take all but the last part to remove the timezone
                date_str_no_tz = " ".join(date_str.split()[:-1])
                date_obj = datetime.strptime(date_str_no_tz, "%a, %d %b %Y %H:%M:%S")
                episode_data["date"] = date_obj
            except (ValueError, IndexError) as e:
                print(f"Could not parse date: {date_str}, error: {e}")
                continue

        # MP3 URL
        enclosure_tag = item.find("enclosure", type="audio/mpeg")
        if enclosure_tag and enclosure_tag.has_attr("url"):
            episode_data["audio_url"] = enclosure_tag["url"]
        else:
            continue  # Skip episodes without audio

        # Episode link (the web page for this episode)
        link_tag = item.find("link")
        if link_tag:
            episode_data["link"] = link_tag.get_text(strip=True)

        # Description
        description_tag = item.find("description")
        if description_tag:
            episode_data["description"] = description_tag.get_text(strip=True)

        # iTunes-specific metadata
        itunes_duration_tag = item.find("itunes:duration")
        if itunes_duration_tag:
            episode_data["duration"] = itunes_duration_tag.get_text(strip=True)

        itunes_episode_tag = item.find("itunes:episode")
        if itunes_episode_tag:
            episode_data["episode_number"] = itunes_episode_tag.get_text(strip=True)

        itunes_subtitle_tag = item.find("itunes:subtitle")
        if itunes_subtitle_tag:
            episode_data["subtitle"] = itunes_subtitle_tag.get_text(strip=True)

        # GUID (unique identifier)
        guid_tag = item.find("guid")
        if guid_tag:
            episode_data["guid"] = guid_tag.get_text(strip=True)

        # Only add episodes that have the minimum required fields
        if "title" in episode_data and "date" in episode_data and "audio_url" in episode_data:
            episodes.append(episode_data)

    print(f"Found {len(episodes)} episodes.")
    return episodes


def parse_date_input(date_input: str) -> Optional[datetime]:
    """Parse various date input formats into a datetime object."""
    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",           # 2025-07-08
        "%Y-%m-%dT%H:%M:%S",  # 2025-07-08T07:00:00
        "%d/%m/%Y",           # 08/07/2025
        "%d-%m-%Y",           # 08-07-2025
        "%Y/%m/%d",           # 2025/07/08
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_input, fmt)
        except ValueError:
            continue
    
    return None


def list_episodes_in_range(
    start_date_str: str, 
    end_date_str: str
) -> List[Dict[str, str]]:
    """
    Lists podcast episodes within a given date range.
    - If no dates are provided, lists episodes from the last 3 months.
    - If only a start date is provided, lists episodes from that date until today.
    - If only an end date is provided, lists episodes from 3 months ago to the specified end date.
    - The date range cannot exceed 12 months.
    """
    today = datetime.now().date()
    
    end_date: date
    if end_date_str:
        parsed_end = parse_date_input(end_date_str)
        if not parsed_end:
            raise ValueError(f"Invalid end_date format: {end_date_str}")
        end_date = parsed_end.date()
    else:
        end_date = today

    start_date: date
    if start_date_str:
        parsed_start = parse_date_input(start_date_str)
        if not parsed_start:
            raise ValueError(f"Invalid start_date format: {start_date_str}")
        start_date = parsed_start.date()
    else:
        # Default to 3 months ago (approx 90 days)
        start_date = today - timedelta(days=90)

    if (end_date - start_date) > timedelta(days=366):
        raise ValueError("The date range cannot exceed 12 months.")

    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date.")

    all_episodes = fetch_podcast_episodes()
    
    filtered_episodes = []
    for episode in all_episodes:
        episode_date = episode['date'].date()
        if start_date <= episode_date <= end_date:
            filtered_episodes.append({
                "episode_name": episode['title'],
                "date": episode_date.isoformat(),
            })
    
    # Sort by date ascending
    filtered_episodes.sort(key=lambda e: e['date'])
    
    return filtered_episodes


def get_episode_info_by_date(date_input: str) -> Optional[Dict]:
    """
    Get episode information by date.
    
    Args:
        date_input: Date string in various formats (YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.)
        
    Returns:
        Dictionary with episode information or None if not found
    """
    # Parse the input date
    target_date = parse_date_input(date_input)
    if not target_date:
        return None
    
    # Fetch episodes from RSS feed
    episodes = fetch_podcast_episodes()
    
    # Find episode by date (matching by date only, ignoring time)
    for episode in episodes:
        if episode["date"].date() == target_date.date():
            # Convert datetime to ISO string for JSON serialization
            episode_copy = episode.copy()
            episode_copy["date"] = episode["date"].isoformat()
            return episode_copy
    
    return None
