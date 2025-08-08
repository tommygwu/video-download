# Fallback Mechanism Documentation

## Overview

The API implements an intelligent fallback mechanism to ensure video downloads succeed even when YouTube's bot detection or other restrictions block certain access methods.

## Default Fallback Order

The system attempts methods in this order:

1. **TV Client** - High quality (up to 4K/2160p) with excellent reliability
2. **iOS Client** - High quality (up to 4K/2160p) but may trigger bot detection
3. **Cookie Authentication** - Bypasses restrictions with authentication
4. **Android Client** - Most reliable but limited to 360p

## How It Works

When a download request is made:

1. The system tries the first method in the fallback order
2. If it encounters bot detection or other errors, it automatically tries the next method
3. This continues until either:
   - A method succeeds (download completes)
   - All methods fail (returns error to user)

## Client Capabilities

| Client  | Max Resolution | Reliability | Notes |
|---------|---------------|-------------|-------|
| TV      | 2160p (4K)    | High        | Best balance of quality and reliability |
| iOS     | 2160p (4K)    | Medium      | High quality, may trigger bot detection |
| Cookies | Varies        | High        | Depends on account status |
| Android | 360p          | Very High   | Always works but poor quality |

## Configuration

### Environment Variables

```bash
# Set custom fallback order (default: tv,ios,cookies,android)
FALLBACK_ORDER=tv,ios,cookies,android

# Set default player client (default: tv)
DEFAULT_PLAYER_CLIENT=tv

# Enable/disable cookie fallback (default: true)
USE_COOKIES_FALLBACK=true

# Provide YouTube cookies in base64 format
YOUTUBE_COOKIES_BASE64=<base64_encoded_cookies>
```

### API Request Options

You can specify a preferred client in your API request:

```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "player_client": "ios"  // or "tv", "android", "cookies", "auto"
}
```

- If `player_client` is specified, it will be tried first
- If it fails, the system continues with the remaining fallback methods
- Use `"auto"` or omit the parameter to use the default fallback order

## Logs

The API logs show the fallback process:

```
[2025-08-08 22:21:00] INFO: Attempting download with method: tv
[2025-08-08 22:21:02] INFO: ✅ Download successful with tv
```

Or if TV fails:

```
[2025-08-08 22:21:00] INFO: Attempting download with method: tv
[2025-08-08 22:21:02] WARNING: ❌ tv failed: Unable to extract video
[2025-08-08 22:21:02] INFO: Attempting download with method: ios
[2025-08-08 22:21:04] INFO: ✅ Download successful with ios
```

## Troubleshooting

### All Methods Failing

If all methods fail, consider:

1. **Add Cookie Authentication**: Export cookies from a logged-in browser session
2. **Check Video Availability**: Some videos may be:
   - Private or deleted
   - Age-restricted (requires authentication)
   - Region-blocked
   - Members-only content

### Poor Quality with Android

The Android client is limited to 360p by YouTube's restrictions. To get higher quality:

1. Ensure iOS and TV clients are in your fallback order
2. Set up cookie authentication for best results
3. Consider using a YouTube Premium account with cookies

### Bot Detection Issues

If you frequently hit bot detection:

1. Reduce request frequency
2. Use cookie authentication
3. Rotate between different client methods
4. Consider implementing request delays

## Testing

Test the fallback mechanism:

```bash
# Test with specific client
python3 test_fallback_mechanism.py

# Test format availability
python3 test_all_clients.py

# Test API with fallback
python3 test_fallback_fix.py
```

## Best Practices

1. **Production Setup**: Always configure cookie authentication for production
2. **Quality vs Reliability**: Balance your fallback order based on needs
   - For best balance (default): `tv,ios,cookies,android`
   - For maximum quality: `ios,tv,cookies,android`
   - For maximum reliability: `tv,cookies,android,ios`
3. **Monitor Logs**: Watch for patterns in failures to adjust the order
4. **Update Regularly**: Keep yt-dlp updated as YouTube changes frequently

## Future Improvements

- Support for PO Tokens (Proof of Origin) for better reliability
- Automatic cookie refresh mechanisms
- Smart fallback order based on video characteristics
- Caching of working methods per video source