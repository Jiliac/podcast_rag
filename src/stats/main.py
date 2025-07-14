import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

TRANSCRIPTIONS_PATH = "data/transcriptions.json"

def load_transcriptions() -> List[Dict[str, Any]]:
    """Load transcriptions from the JSON file."""
    if not os.path.exists(TRANSCRIPTIONS_PATH):
        print(f"Error: Transcriptions file not found at {TRANSCRIPTIONS_PATH}")
        return []
    
    try:
        with open(TRANSCRIPTIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {TRANSCRIPTIONS_PATH}")
        return []

def parse_episode_date(date_str: str) -> Optional[datetime]:
    """Parse episode date from ISO format string."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def calculate_episode_coverage_stats(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about episode coverage."""
    if not episodes:
        return {
            "total_episodes": 0,
            "date_range": None,
            "earliest_episode": None,
            "latest_episode": None,
            "period_covered_days": 0,
            "average_episodes_per_month": 0
        }
    
    # Parse dates and filter valid ones
    dated_episodes = []
    for episode in episodes:
        date_obj = parse_episode_date(episode.get('date', ''))
        if date_obj:
            dated_episodes.append((episode, date_obj))
    
    if not dated_episodes:
        return {
            "total_episodes": len(episodes),
            "date_range": "No valid dates found",
            "earliest_episode": None,
            "latest_episode": None,
            "period_covered_days": 0,
            "average_episodes_per_month": 0
        }
    
    # Sort by date
    dated_episodes.sort(key=lambda x: x[1])
    
    earliest_episode, earliest_date = dated_episodes[0]
    latest_episode, latest_date = dated_episodes[-1]
    
    # Calculate period covered
    period_covered = latest_date - earliest_date
    days_covered = period_covered.days
    
    # Calculate average episodes per month
    if days_covered > 0:
        months_covered = days_covered / 30.44  # Average days per month
        avg_episodes_per_month = len(dated_episodes) / months_covered if months_covered > 0 else 0
    else:
        avg_episodes_per_month = 0
    
    return {
        "total_episodes": len(episodes),
        "episodes_with_dates": len(dated_episodes),
        "date_range": f"{earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}",
        "earliest_episode": {
            "title": earliest_episode.get('title', 'Unknown'),
            "date": earliest_date.strftime('%Y-%m-%d')
        },
        "latest_episode": {
            "title": latest_episode.get('title', 'Unknown'),
            "date": latest_date.strftime('%Y-%m-%d')
        },
        "period_covered_days": days_covered,
        "average_episodes_per_month": round(avg_episodes_per_month, 2)
    }

def calculate_content_analysis_stats(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics about episode content."""
    if not episodes:
        return {
            "total_transcriptions": 0,
            "total_words": 0,
            "total_characters": 0,
            "average_words_per_episode": 0,
            "average_characters_per_episode": 0,
            "shortest_episode": None,
            "longest_episode": None
        }
    
    transcriptions = []
    for episode in episodes:
        transcription = episode.get('transcription', '')
        if transcription and transcription.strip():
            word_count = len(transcription.split())
            char_count = len(transcription)
            transcriptions.append({
                "title": episode.get('title', 'Unknown'),
                "words": word_count,
                "characters": char_count,
                "transcription": transcription
            })
    
    if not transcriptions:
        return {
            "total_transcriptions": 0,
            "total_words": 0,
            "total_characters": 0,
            "average_words_per_episode": 0,
            "average_characters_per_episode": 0,
            "shortest_episode": None,
            "longest_episode": None
        }
    
    # Calculate totals
    total_words = sum(t['words'] for t in transcriptions)
    total_characters = sum(t['characters'] for t in transcriptions)
    
    # Find shortest and longest episodes
    shortest = min(transcriptions, key=lambda x: x['words'])
    longest = max(transcriptions, key=lambda x: x['words'])
    
    return {
        "total_transcriptions": len(transcriptions),
        "total_words": total_words,
        "total_characters": total_characters,
        "average_words_per_episode": round(total_words / len(transcriptions), 0),
        "average_characters_per_episode": round(total_characters / len(transcriptions), 0),
        "shortest_episode": {
            "title": shortest['title'],
            "words": shortest['words'],
            "characters": shortest['characters']
        },
        "longest_episode": {
            "title": longest['title'],
            "words": longest['words'],
            "characters": longest['characters']
        }
    }

def calculate_data_quality_stats(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate data quality metrics."""
    if not episodes:
        return {
            "total_episodes": 0,
            "episodes_with_transcriptions": 0,
            "episodes_with_dates": 0,
            "episodes_with_audio_urls": 0,
            "completion_percentage": 0,
            "missing_data": []
        }
    
    episodes_with_transcriptions = 0
    episodes_with_dates = 0
    episodes_with_audio_urls = 0
    missing_data = []
    
    for i, episode in enumerate(episodes):
        episode_issues = []
        
        # Check transcription
        transcription = episode.get('transcription', '')
        if transcription and transcription.strip():
            episodes_with_transcriptions += 1
        else:
            episode_issues.append("missing_transcription")
        
        # Check date
        date_str = episode.get('date', '')
        if date_str and parse_episode_date(date_str):
            episodes_with_dates += 1
        else:
            episode_issues.append("missing_or_invalid_date")
        
        # Check audio URL
        audio_url = episode.get('audio_url', '')
        if audio_url and audio_url.strip():
            episodes_with_audio_urls += 1
        else:
            episode_issues.append("missing_audio_url")
        
        if episode_issues:
            missing_data.append({
                "episode_index": i,
                "title": episode.get('title', 'Unknown'),
                "issues": episode_issues
            })
    
    # Calculate completion percentage
    total_fields = len(episodes) * 3  # 3 fields per episode (transcription, date, audio_url)
    complete_fields = episodes_with_transcriptions + episodes_with_dates + episodes_with_audio_urls
    completion_percentage = (complete_fields / total_fields * 100) if total_fields > 0 else 0
    
    return {
        "total_episodes": len(episodes),
        "episodes_with_transcriptions": episodes_with_transcriptions,
        "episodes_with_dates": episodes_with_dates,
        "episodes_with_audio_urls": episodes_with_audio_urls,
        "completion_percentage": round(completion_percentage, 1),
        "missing_data": missing_data
    }

def print_stats(stats: Dict[str, Any]) -> None:
    """Print statistics in a formatted way."""
    print("=" * 60)
    print("PODCAST EPISODE STATISTICS")
    print("=" * 60)
    
    # Episode Coverage Statistics
    coverage = stats['coverage']
    print("\n📊 EPISODE COVERAGE")
    print(f"   Total Episodes: {coverage['total_episodes']}")
    print(f"   Episodes with Dates: {coverage['episodes_with_dates']}")
    print(f"   Period Covered: {coverage['date_range']}")
    print(f"   Duration: {coverage['period_covered_days']} days")
    print(f"   Average Episodes/Month: {coverage['average_episodes_per_month']}")
    
    if coverage['earliest_episode']:
        print(f"   Earliest Episode: {coverage['earliest_episode']['title']}")
        print(f"                    ({coverage['earliest_episode']['date']})")
    
    if coverage['latest_episode']:
        print(f"   Latest Episode: {coverage['latest_episode']['title']}")
        print(f"                  ({coverage['latest_episode']['date']})")
    
    # Content Analysis Statistics
    content = stats['content']
    print("\n📝 CONTENT ANALYSIS")
    print(f"   Episodes with Transcriptions: {content['total_transcriptions']}")
    print(f"   Total Words: {content['total_words']:,}")
    print(f"   Total Characters: {content['total_characters']:,}")
    print(f"   Average Words per Episode: {content['average_words_per_episode']:,}")
    print(f"   Average Characters per Episode: {content['average_characters_per_episode']:,}")
    
    if content['shortest_episode']:
        print(f"   Shortest Episode: {content['shortest_episode']['title']}")
        print(f"                    ({content['shortest_episode']['words']:,} words)")
    
    if content['longest_episode']:
        print(f"   Longest Episode: {content['longest_episode']['title']}")
        print(f"                   ({content['longest_episode']['words']:,} words)")
    
    # Data Quality Statistics
    quality = stats['quality']
    print("\n✅ DATA QUALITY")
    print(f"   Total Episodes: {quality['total_episodes']}")
    print(f"   Episodes with Transcriptions: {quality['episodes_with_transcriptions']}")
    print(f"   Episodes with Dates: {quality['episodes_with_dates']}")
    print(f"   Episodes with Audio URLs: {quality['episodes_with_audio_urls']}")
    print(f"   Overall Completion: {quality['completion_percentage']}%")
    
    if quality['missing_data']:
        print(f"\n⚠️  MISSING DATA ({len(quality['missing_data'])} episodes)")
        for item in quality['missing_data']:
            issues = ", ".join(item['issues'])
            print(f"   - {item['title']}: {issues}")
    
    print("\n" + "=" * 60)

def main():
    """Main function to generate and display statistics."""
    print("Loading transcriptions...")
    episodes = load_transcriptions()
    
    if not episodes:
        print("No episodes found. Exiting.")
        return
    
    print(f"Loaded {len(episodes)} episodes. Calculating statistics...")
    
    # Calculate all statistics
    stats = {
        'coverage': calculate_episode_coverage_stats(episodes),
        'content': calculate_content_analysis_stats(episodes),
        'quality': calculate_data_quality_stats(episodes)
    }
    
    # Print results
    print_stats(stats)
    
    # Optional: Save to JSON file
    if "--export" in sys.argv:
        output_file = "data/podcast_stats.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"\nStats exported to {output_file}")

if __name__ == "__main__":
    main()