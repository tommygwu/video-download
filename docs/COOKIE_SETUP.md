# YouTube Cookie Export and Setup Guide

⚠️ **SECURITY WARNING**: YouTube cookies can provide access to your Google account! Read the [Cookie Security Guide](COOKIE_SECURITY.md) before proceeding.

This guide explains how to export YouTube cookies from your local browser and configure them for the API running on Render.com.

## Overview

The API now supports three methods to bypass YouTube bot detection:
1. **iOS Player Client** (default) - Works without authentication ✅ SAFEST
2. **Cookie Authentication** (fallback) - Uses your YouTube login ⚠️ SECURITY RISK
3. **Android Player Client** (last resort) - Limited quality but reliable ✅ SAFE

## Cookie Export Process

### Step 1: Choose Security Level

The updated script offers three security levels:

```bash
cd /Users/twu/GitHub/video-download

# RECOMMENDED: Minimal cookies (safest)
python3 export_youtube_cookies.py --level minimal

# For age-restricted content
python3 export_youtube_cookies.py --level age-restricted

# DANGEROUS: All cookies (includes Google account auth)
python3 export_youtube_cookies.py --level full --skip-warning
```

**Security Levels:**
- **minimal** - Only essential YouTube cookies (VISITOR_INFO1_LIVE, YSC, PREF)
- **age-restricted** - Adds LOGIN_INFO for restricted content
- **full** - ALL cookies including Google account session (DANGEROUS)

The script will:
- Show security warnings and require confirmation
- Extract ONLY the selected cookie level
- Exclude dangerous cookies by default
- Create files on your Desktop with the security level in the filename

### Step 2: Configure Render.com

1. Open `youtube_cookies_base64.txt` from your Desktop
2. Copy the entire content (it's one long line)
3. Go to your Render.com dashboard
4. Navigate to your service → Environment
5. Add a new environment variable:
   - Key: `YOUTUBE_COOKIES_BASE64`
   - Value: [paste the copied base64 string]
6. Save and deploy

### Step 3: Configure Fallback Order (Optional)

You can customize the fallback order by setting these environment variables in Render.com:

```bash
# Default player client (ios, android, mweb, web, cookies)
DEFAULT_PLAYER_CLIENT=ios

# Fallback order (comma-separated)
FALLBACK_ORDER=ios,cookies,android

# Enable/disable cookie fallback
USE_COOKIES_FALLBACK=true
```

## API Usage

### Using Default Configuration (iOS → Cookies → Android)

```bash
curl -X POST https://your-api.onrender.com/api/download \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID"
  }'
```

### Force Cookie Authentication

```bash
curl -X POST https://your-api.onrender.com/api/download \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "player_client": "cookies"
  }'
```

### Available Player Clients

- `ios` - Best quality, no auth needed (default)
- `cookies` - Uses your YouTube login
- `android` - Limited to 360p
- `mweb` - Mobile web, limited to 360p
- `web` - Standard web (may trigger bot detection)

## Security Notes

1. **Only YouTube cookies are exported** - The script filters for `.youtube.com` domains only
2. **Cookies are stored as environment variables** - Not in code
3. **Temporary files are cleaned up** - Cookie files are deleted after use
4. **Cookies expire** - You'll need to re-export every 2-3 weeks

## Troubleshooting

### Chrome Cookies Not Found

If the script can't find Chrome cookies:
1. Make sure Chrome is installed
2. Make sure you're logged into YouTube in Chrome
3. Try closing Chrome before running the script
4. Manually specify the path when prompted

### Cookies Not Working

If cookies authentication fails:
1. Make sure you're logged into YouTube in Chrome
2. Re-export cookies (they may have expired)
3. Check Render.com logs for specific errors
4. Try using iOS client instead

### Dependencies for Cookie Export

If you get import errors, install required packages:

```bash
pip3 install pycryptodome keyring
```

## Cookie File Format

The exported cookies are in Netscape HTTP Cookie format:
```
# Netscape HTTP Cookie File
.youtube.com    TRUE    /    TRUE    1234567890    cookie_name    cookie_value
```

## Monitoring

The API logs which authentication method is being used:

```
[2025-08-08 21:30:00] INFO: Using player client: ios
[2025-08-08 21:30:05] INFO: iOS client failed, trying cookies
[2025-08-08 21:30:06] INFO: Using cookie authentication
[2025-08-08 21:30:10] INFO: Download successful with cookies
```

## Alternative: Manual Cookie Export

If the automated script doesn't work, you can use Chrome extensions:

1. Install "Get cookies.txt LOCALLY" from Chrome Web Store
2. Navigate to YouTube and log in
3. Click the extension and export cookies
4. Convert to base64: `base64 -i cookies.txt -o cookies_base64.txt`
5. Copy content to Render.com environment variable

## FAQ

**Q: How often do I need to update cookies?**
A: YouTube cookies typically last 2-3 weeks. Update when downloads start failing.

**Q: Is this secure?**
A: Yes, only YouTube cookies are exported and they're stored securely as environment variables.

**Q: Can I use Firefox instead of Chrome?**
A: The script currently supports Chrome only, but you can use Firefox extensions to export cookies manually.

**Q: What if both iOS and cookies fail?**
A: The API will automatically fall back to Android client (360p quality).

**Q: Can I disable cookie fallback?**
A: Yes, set `USE_COOKIES_FALLBACK=false` in Render.com environment variables.