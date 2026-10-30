# Sigabo Auto M3U Updater

Simple GitHub Actions + script that automatically finds the latest **Coco Martin's Sigabo** episodes from the official ABS-CBN Entertainment YouTube channel and updates an M3U playlist using clean `https://www.youtube.com/watch?v=VIDEO_ID` links.

## Features
- Uses only official public YouTube watch links (the format you requested)
- Does **not** remove existing entries unless you want it to
- GitHub Actions can run on schedule (every hour / daily)
- You control the `#EXTINF` title, group, logo, etc.

## Quick Start

### 1. Local use
```bash
# Install yt-dlp first
pip install yt-dlp

# Run once
python update_sigabo.py
```

This will create / update `sigabo.m3u` with the newest episodes found.

### 2. GitHub Automatic
1. Create a new public/private repository on GitHub.
2. Upload all files from this zip (including the `.github` folder).
3. Go to **Actions** tab → enable workflows if needed.
4. The workflow runs every day at 01:00 UTC (you can change the cron).
5. After it runs, the updated `sigabo.m3u` will be committed back to the repo.
6. Use the raw link in your IPTV player:
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/sigabo.m3u
   ```

## Customization
Edit `update_sigabo.py`:
- `MAX_EPISODES` – how many recent episodes to keep
- `SEARCH_QUERY` – change search terms if needed
- `#EXTINF` template – add logo, tvg-id, group-title, etc.

## Notes
- Relies on yt-dlp (very reliable for public YouTube videos).
- Only uses publicly available videos from the official channel.
- You still decide the final titles and order.