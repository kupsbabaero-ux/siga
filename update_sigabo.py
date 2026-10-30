#!/usr/bin/env python3
"""
Sigabo Auto M3U Updater
- Kinukuha ang LAHAT ng episode mula Episode 1 hanggang latest
- HINDI tinatanggal ang existing entries
- Mag-a-append lang ng mga bagong video na wala pa sa listahan
- Pure https://www.youtube.com/watch?v=VIDEO_ID format
"""

import subprocess
import json
import os
import re
from datetime import datetime

# ============== CONFIG ==============
# Primary official playlist
PLAYLIST_URLS = [
    "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj7u_vo-pkqn4TcyZ3UkEHfD",  # Main
    "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj4PYVq_kWW6FMreGkEEmr_L",  # Kapamilya Online Live
]

OUTPUT_FILE = "sigabo.m3u"
# ====================================

def run_yt_dlp(url):
    """Fetch playlist entries"""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"Warning: yt-dlp error for {url[:60]}...")
            return []
        data = json.loads(result.stdout)
        return data.get("entries", []) or []
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install with:  pip install yt-dlp")
        return []
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def extract_episode_number(title: str) -> int:
    """Extract episode number for sorting"""
    patterns = [
        r'(?:episode|ep\.?)\s*(\d+)',
        r'ep\.?\s*(\d+)',
        r'#(\d+)',
    ]
    for p in patterns:
        match = re.search(p, title, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 9999

def load_existing_ids(filepath):
    """Basahin ang existing M3U at kunin ang lahat ng video IDs (para hindi ma-duplicate / ma-remove)"""
    existing_ids = set()
    existing_lines = []
    if not os.path.exists(filepath):
        return existing_ids, existing_lines

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Keep the whole file content so we never lose anything
    existing_lines = content.strip().splitlines()

    for line in existing_lines:
        line = line.strip()
        if "youtube.com/watch?v=" in line:
            match = re.search(r'v=([a-zA-Z0-9_-]{11})', line)
            if match:
                existing_ids.add(match.group(1))
    return existing_ids, existing_lines

def make_extinf(title: str) -> str:
    clean_title = title.replace("|", "-").strip()
    return f'#EXTINF:-1 tvg-id="sigabo" group-title="Kapamilya - Sigabo",{clean_title}'

def main():
    print(f"[{datetime.now()}] Starting Sigabo updater...")
    print("Mode: KEEP ALL existing + ADD new episodes only (walang tinatanggal)")

    # 1. Load existing M3U (para hindi mawala ang kahit anong entry)
    existing_ids, existing_lines = load_existing_ids(OUTPUT_FILE)
    print(f"Existing videos sa M3U: {len(existing_ids)}")

    # 2. Fetch from all playlists
    all_entries = []
    for url in PLAYLIST_URLS:
        print(f"Fetching: {url}")
        entries = run_yt_dlp(url)
        all_entries.extend(entries)
        print(f"  → {len(entries)} entries")

    if not all_entries:
        print("No new data from playlists. Existing M3U is kept as-is.")
        return

    # 3. Collect new videos only
    new_videos = []
    seen = set(existing_ids)

    for e in all_entries:
        title = (e.get("title") or "").strip()
        vid = e.get("id")
        if not vid or not title:
            continue
        if vid in seen:
            continue
        # Accept anything that looks like Sigabo episode
        if "sigabo" not in title.lower():
            continue
        seen.add(vid)
        new_videos.append({
            "id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "ep": extract_episode_number(title)
        })

    # Sort new ones by episode number
    new_videos.sort(key=lambda x: (x["ep"], x["title"]))

    print(f"New Sigabo videos found: {len(new_videos)}")

    if not new_videos and existing_lines:
        print("Walang bagong episode. Existing M3U is untouched.")
        return

    # 4. Build final M3U
    # Keep header + all previous content, then append new ones
    lines = []

    if existing_lines:
        # Keep everything that was already there
        lines = existing_lines[:]
        # Remove trailing empty lines
        while lines and lines[-1].strip() == "":
            lines.pop()
        lines.append("")
        lines.append(f"# --- New episodes added: {datetime.now().isoformat()} ---")
    else:
        # First time create
        lines = [
            "#EXTM3U",
            f"# Generated: {datetime.now().isoformat()}",
            "# Source: Official ABS-CBN Entertainment playlists",
            "# Format: pure youtube.com/watch?v= links",
            "# Mode: never removes existing entries",
            ""
        ]

    for v in new_videos:
        lines.append(make_extinf(v["title"]))
        lines.append(v["url"])
        lines.append("")

    # Write back
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done. Added {len(new_videos)} new videos.")
    print(f"Total unique videos now: {len(existing_ids) + len(new_videos)}")
    print("Existing entries were NOT removed.")

if __name__ == "__main__":
    main()
