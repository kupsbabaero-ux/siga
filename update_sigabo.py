#!/usr/bin/env python3
"""
Sigabo Auto M3U Updater
Fetches ALL Coco Martin's Sigabo episodes (from Episode 1 to latest)
from the official ABS-CBN Entertainment playlist and writes
clean https://www.youtube.com/watch?v=VIDEO_ID links into sigabo.m3u

Does NOT remove previous entries — it rebuilds the complete list every run.
"""

import subprocess
import json
import os
import re
from datetime import datetime

# ============== CONFIG ==============
# Official main playlist for Coco Martin's Sigabo
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj7u_vo-pkqn4TcyZ3UkEHfD"

# Alternative (Kapamilya Online Live Sigabo playlist - more parts)
# PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj4PYVq_kWW6FMreGkEEmr_L"

OUTPUT_FILE = "sigabo.m3u"
# ====================================

def run_yt_dlp():
    """Fetch entire playlist"""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        PLAYLIST_URL,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
        data = json.loads(result.stdout)
        return data.get("entries", [])
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install with:  pip install yt-dlp")
        return []
    except Exception as e:
        print(f"ERROR running yt-dlp: {e}")
        return []

def extract_episode_number(title: str):
    """Try to extract episode number for sorting"""
    # Common patterns: Episode 91, Ep. 91, EP 91, Episode 91 (1/3)
    match = re.search(r'(?:episode|ep\.?)\s*(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 9999  # put unknown at the end

def make_extinf(title: str) -> str:
    clean_title = title.replace("|", "-").strip()
    return f'#EXTINF:-1 tvg-id="sigabo" group-title="Kapamilya - Sigabo",{clean_title}'

def main():
    print(f"[{datetime.now()}] Fetching ALL Sigabo episodes from official playlist...")
    entries = run_yt_dlp()

    if not entries:
        print("No videos found. Check playlist URL or yt-dlp installation.")
        return

    # Keep only real video entries and unique IDs
    seen = set()
    videos = []
    for e in entries:
        title = (e.get("title") or "").strip()
        vid = e.get("id")
        if not vid or not title or vid in seen:
            continue
        # Filter out non-episode content if needed
        if "sigabo" not in title.lower():
            continue
        seen.add(vid)
        videos.append({
            "id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "ep": extract_episode_number(title)
        })

    # Sort by episode number (Episode 1 → latest)
    videos.sort(key=lambda x: (x["ep"], x["title"]))

    print(f"Found {len(videos)} Sigabo videos (Episode 1 to current).")

    # Write complete M3U (full rebuild – nothing is removed permanently)
    lines = [
        "#EXTM3U",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Total episodes/parts: {len(videos)}",
        f"# Source: {PLAYLIST_URL}",
        "# Format: pure youtube.com/watch?v= links",
        ""
    ]

    for v in videos:
        lines.append(make_extinf(v["title"]))
        lines.append(v["url"])
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Updated {OUTPUT_FILE} successfully with ALL episodes.")
    print("Oldest → Newest order.")

if __name__ == "__main__":
    main()
