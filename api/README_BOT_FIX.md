# YouTube Bot Detection Fix for API

## Changes Made

The API has been updated to bypass YouTube's bot detection that shows "Sign in to confirm you're not a bot" error.

### What Was Changed

All three API endpoints (`/api/info`, `/api/download`, `/api/stream`) now support:

1. **Default iOS player client** - Automatically uses iOS client which bypasses bot detection
2. **Configurable player client** - Can specify `player_client` in API requests
3. **Multiple client options** - Supports `ios`, `android`, `mweb`, and `web` clients

### API Request Format

All endpoints now accept an optional `player_client` parameter:

```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "player_client": "ios"  // Optional, defaults to "ios"
}
```

### Available Player Clients

- **`ios`** (default) - Best quality, supports up to 4K, uses HLS format
- **`android`** - Limited to 360p but very reliable
- **`mweb`** - Mobile web, limited to 360p
- **`web`** - Standard web client (may trigger bot detection)

### Example API Calls

#### Get Video Info
```bash
curl -X POST http://localhost:5000/api/info \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "player_client": "ios"
  }'
```

#### Download Video
```bash
curl -X POST http://localhost:5000/api/download \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "best[ext=mp4]/best",
    "player_client": "ios"
  }' \
  --output video.mp4
```

### Testing the Fix

Run the test script to verify the bot detection bypass is working:

```bash
# Start the API server
python3 api/app.py

# In another terminal, run the test
python3 test_api_bot_fix.py
```

### Fallback Options

If you still encounter issues with certain videos:

1. **Use Android client** - More restricted but often works when iOS doesn't
2. **Add cookie authentication** - Future enhancement to support browser cookies
3. **Use PO Tokens** - Advanced option for persistent access (requires additional setup)

### Notes

- The iOS client provides the best quality but uses HLS (m3u8) format which yt-dlp automatically handles
- Some videos may have additional restrictions beyond bot detection (age-gated, region-locked, etc.)
- The fix works for most YouTube videos but edge cases may still require authentication

### Monitoring

The API logs now show which player client is being used:
```
[2025-08-08 21:30:00] INFO in app: Using player client: ios
[2025-08-08 21:30:00] INFO in app: Starting download for URL: https://youtube.com/...
[2025-08-08 21:30:00] INFO in app: Player client: ios
```