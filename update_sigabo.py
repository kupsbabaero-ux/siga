#!/usr/bin/env python3
"""
Sigabo Auto M3U Updater
- EPISODE lang ang isasama (hindi highlights, recap, teaser, etc.)
- Episode 1 hanggang latest
- HINDI tinatanggal ang existing entries
- Mag-a-append lang ng mga wala pa
"""

import subprocess
import json
import os
import re
from datetime import datetime

OUTPUT_FILE = "sigabo.m3u"

SOURCES = [
    "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj7u_vo-pkqn4TcyZ3UkEHfD",
    "https://www.youtube.com/playlist?list=PLPcB0_P-Zlj4PYVq_kWW6FMreGkEEmr_L",
    "ytsearch200:Coco Martin's Sigabo Episode",
]

def run_yt_dlp(src):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        "--ignore-errors",
        src,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        return data.get("entries", []) or []
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install: pip install yt-dlp")
        return []
    except Exception as e:
        print(f"Warning: {e}")
        return []

def extract_episode_number(title: str) -> int:
    m = re.search(r'(?:episode|ep\.?)\s*(\d+)', title, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 9999

def is_real_episode(title: str) -> bool:
    """Episode lang — i-reject ang highlights, recap, teaser, behind the scenes, etc."""
    t = title.lower()

    # Must contain sigabo + episode/ep
    if "sigabo" not in t:
        return False
    if not re.search(r'(?:episode|ep\.?)\s*\d+', t):
        return False

    # Reject non-episode content
    reject_keywords = [
        "highlight", "highlights", "recap", "teaser", "trailer",
        "behind the scenes", "bts", "exclusive", "interview",
        "scene rewind", "trending scene", "quick feel", "reaction",
        "review", "preview", "promo", "cast", "meet the",
        "making of", "bloopers", "outtake"
    ]
    for kw in reject_keywords:
        if kw in t:
            return False

    return True

def load_existing(filepath):
    existing_ids = set()
    existing_lines = []
    if not os.path.exists(filepath):
        return existing_ids, existing_lines

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    existing_lines = content.strip().splitlines()

    for line in existing_lines:
        if "youtube.com/watch?v=" in line:
            m = re.search(r'v=([a-zA-Z0-9_-]{11})', line)
            if m:
                existing_ids.add(m.group(1))
    return existing_ids, existing_lines

def make_extinf(title: str) -> str:
    clean = title.replace("|", "-").strip()
    return f'#EXTINF:-1 tvg-id="sigabo" group-title="Kapamilya - Sigabo",{clean}'

def main():
    print(f"[{datetime.now()}] Sigabo updater")
    print("Mode: EPISODE only + keep existing + append new\n")

    existing_ids, existing_lines = load_existing(OUTPUT_FILE)
    print(f"Existing videos: {len(existing_ids)}")

    all_entries = []
    for src in SOURCES:
        print(f"Fetching → {src[:65]}...")
        entries = run_yt_dlp(src)
        print(f"   got {len(entries)}")
        all_entries.extend(entries)

    new_videos = []
    seen = set(existing_ids)

    for e in all_entries:
        if not e:
            continue
        title = (e.get("title") or "").strip()
        vid = e.get("id")
        if not vid or not title or vid in seen:
            continue
        if not is_real_episode(title):
            continue

        seen.add(vid)
        new_videos.append({
            "id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "ep": extract_episode_number(title)
        })

    new_videos.sort(key=lambda x: (x["ep"], x["title"]))

    print(f"\nNew real episodes to add: {len(new_videos)}")

    if not new_videos:
        print("Walang bagong episode. Existing M3U is safe (walang tinanggal).")
        return

    if existing_lines:
        lines = existing_lines[:]
        while lines and lines[-1].strip() == "":
            lines.pop()
        lines.append("")
        lines.append(f"# --- Added {len(new_videos)} episodes on {datetime.now().isoformat()} ---")
    else:
        lines = [
            "#EXTM3U",
            f"# Generated: {datetime.now().isoformat()}",
            "# Mode: episode only + never removes existing",
            "# Format: pure youtube.com/watch?v= links",
            ""
        ]

    for v in new_videos:
        lines.append(make_extinf(v["title"]))
        lines.append(v["url"])
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done. Added {len(new_videos)} episodes.")
    print(f"Total unique now: {len(existing_ids) + len(new_videos)}")
    print("Existing entries were NOT removed.")

if __name__ == "__main__":
    main()
