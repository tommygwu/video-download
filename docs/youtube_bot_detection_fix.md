# YouTube Bot Detection Fix Guide

## Problem
YouTube shows the error: **"Sign in to confirm you're not a bot"** when using yt-dlp.

## Solution Summary

The most effective solution is to use **mobile clients** (iOS, Android) which bypass bot detection without requiring authentication.

## Working Methods

### 1. iOS Client (RECOMMENDED) ✅
**Best for:** Getting high-quality formats including HD and 4K
```bash
python3 -m yt_dlp --extractor-args "youtube:player_client=ios" [URL]
```
- ✅ Bypasses bot detection
- ✅ Provides all quality formats (up to 4K)
- ✅ No authentication required
- ⚠️ Formats are in HLS (m3u8) which may need conversion

### 2. Android Client ✅
**Best for:** Quick downloads when only basic quality is needed
```bash
python3 -m yt_dlp --extractor-args "youtube:player_client=android" [URL]
```
- ✅ Bypasses bot detection
- ✅ No authentication required
- ❌ Limited to 360p quality
- ⚠️ May require PO Token for higher qualities

### 3. Mobile Web Client ✅
**Alternative option with similar limitations to Android**
```bash
python3 -m yt_dlp --extractor-args "youtube:player_client=mweb" [URL]
```
- ✅ Bypasses bot detection
- ❌ Limited to 360p quality
- ⚠️ May require PO Token for higher qualities

### 4. Cookie Authentication
**Use if you need specific account features**
```bash
# From Chrome
python3 -m yt_dlp --cookies-from-browser chrome [URL]

# From Firefox
python3 -m yt_dlp --cookies-from-browser firefox [URL]

# From Safari (may require permissions)
python3 -m yt_dlp --cookies-from-browser safari [URL]
```

### 5. Combined Approach
**For best compatibility**
```bash
python3 -m yt_dlp --extractor-args "youtube:player_client=ios" --cookies-from-browser chrome [URL]
```

## Quick Scripts

### Interactive Menu Script
A helper script `youtube_bot_fix.sh` is available that provides an interactive menu for all these methods.

```bash
./youtube_bot_fix.sh
```

### Clean Logging Mode
For condensed, meaningful output without health check spam:

```bash
# Direct usage
python3 yt_dlp_clean_logger.py "https://youtube.com/watch?v=..."

# Or use the shell wrapper
./clean_download.sh "https://youtube.com/watch?v=..."

# With options
./clean_download.sh -c ios -v -l download.log "https://youtube.com/watch?v=..."
```

Clean logging provides:
- 🎬 Start/end notifications
- 💚 Server alive status every 5 minutes
- 📊 Progress at 25%, 50%, 75% milestones  
- ✅ Completion confirmation
- 🔇 Silent mode after download
- No health check spam!

## Downloading with iOS Client

To download the best quality video + audio:
```bash
# Download best quality
python3 -m yt_dlp --extractor-args "youtube:player_client=ios" -f "best[ext=mp4]" [URL]

# Download specific quality (e.g., 1080p)
python3 -m yt_dlp --extractor-args "youtube:player_client=ios" -f "270+234" [URL]
```

## Additional Options

### List Available Formats
```bash
python3 -m yt_dlp --extractor-args "youtube:player_client=ios" -F [URL]
```

### Use Browser Impersonation
```bash
python3 -m yt_dlp --impersonate chrome [URL]
```

### Multiple Player Clients
You can try other clients if needed:
- `tv` - TV client
- `web_embedded` - Embedded player
- `android_vr` - Android VR client

## Troubleshooting

1. **Still getting bot detection?**
   - Wait a few hours if your IP is temporarily flagged
   - Try disabling VPN or switching servers
   - Update yt-dlp: `pip install --upgrade yt-dlp`

2. **Cookie errors?**
   - Make sure you're logged into YouTube in the browser
   - Try a different browser for cookie extraction
   - On macOS, you may need to grant terminal permissions for Safari

3. **Format issues with iOS client?**
   - The iOS client provides HLS (m3u8) formats
   - yt-dlp will automatically handle conversion if ffmpeg is installed
   - Install ffmpeg if needed: `brew install ffmpeg`

## Why This Works

YouTube's bot detection primarily targets the default web client. Mobile clients (iOS, Android) use different API endpoints that currently don't trigger the same bot detection mechanisms. This makes them effective for bypassing the "Sign in to confirm you're not a bot" error.

## Notes

- The iOS client provides the best quality options
- Android/mweb clients are limited but reliable for basic downloads
- Cookie authentication helps but isn't always necessary with mobile clients
- These methods may change as YouTube updates their systems