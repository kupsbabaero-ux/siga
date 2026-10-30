#!/usr/bin/env python3
"""
Sigabo Auto M3U Updater
Fetches recent Coco Martin's Sigabo episodes from ABS-CBN Entertainment
and writes clean youtube.com/watch?v= links into sigabo.m3u
"""

import subprocess
import json
import os
from datetime import datetime

# ============== CONFIG ==============
MAX_EPISODES = 30          # how many recent episodes to keep
OUTPUT_FILE = "sigabo.m3u"
SEARCH_QUERY = "Coco Martin's Sigabo"
CHANNEL = "https://www.youtube.com/@ABSCBNEntertainment"
# ====================================

def run_yt_dlp():
    """Search for recent Sigabo videos and return list of dicts"""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end", str(MAX_EPISODES * 3),  # fetch extra because of parts
        f"ytsearch{MAX_EPISODES * 3}:{SEARCH_QUERY} channel:ABS-CBN Entertainment",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data.get("entries", [])
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install with:  pip install yt-dlp")
        return []
    except Exception as e:
        print(f"ERROR running yt-dlp: {e}")
        return []

def is_sigabo(title: str) -> bool:
    title_lower = title.lower()
    return "sigabo" in title_lower and ("coco martin" in title_lower or "episode" in title_lower)

def make_extinf(title: str, video_id: str) -> str:
    # You can customize this line
    clean_title = title.replace("|", "-").strip()
    return f'#EXTINF:-1 tvg-id="sigabo" group-title="Kapamilya - Sigabo",{clean_title}'

def main():
    print(f"[{datetime.now()}] Searching for Sigabo episodes...")
    entries = run_yt_dlp()

    if not entries:
        print("No videos found.")
        return

    # Filter only real Sigabo episodes and keep unique video IDs
    seen = set()
    videos = []
    for e in entries:
        title = e.get("title") or ""
        vid = e.get("id")
        if not vid or vid in seen:
            continue
        if is_sigabo(title):
            seen.add(vid)
            videos.append({
                "id": vid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}"
            })
            if len(videos) >= MAX_EPISODES:
                break

    print(f"Found {len(videos)} Sigabo videos.")

    # Write M3U
    lines = ["#EXTM3U"]
    lines.append(f"# Generated: {datetime.now().isoformat()}")
    lines.append("")

    for v in videos:
        lines.append(make_extinf(v["title"], v["id"]))
        lines.append(v["url"])
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Updated {OUTPUT_FILE} successfully.")

if __name__ == "__main__":
    main()