# API Logging Enhancements

## Overview
Enhanced logging has been added to the yt-dlp API to provide comprehensive visibility into request processing and download operations.

## What's Logged Now

### 1. Request Tracking
Every API request now logs:
- **Request received**: Method, path, client IP, and User-Agent
- **Request body**: URL being processed and format preferences
- **Response status**: HTTP status code and processing time
- **Clear separators**: Visual separators (====) between requests for easy reading

### 2. Download Progress
During video downloads, you'll see:
- **Start of download**: Full URL, format preference, and limits
- **Video metadata**: Title, duration, uploader
- **Progress updates**: Download percentage, speed, and ETA
- **Completion status**: File size, location, and success confirmation

### 3. Server Startup
On server start, logs show:
- Environment (production/development)
- Download directory location
- Maximum file size limits
- File cleanup schedule
- API key configuration status

### 4. Health Checks
Health check requests are also logged to track monitoring activity

## Example Log Output

```
================================================================================
YT-DLP API SERVER STARTED
Environment: production
Download directory: /tmp/downloads
Max file size: 500 MB
File cleanup after: 30 minutes
API Key configured: Yes
================================================================================

[2025-08-08 12:00:00] INFO in app: ============================================================
[2025-08-08 12:00:00] INFO in app: REQUEST RECEIVED: POST /api/download
[2025-08-08 12:00:00] INFO in app: Client IP: 192.168.1.100
[2025-08-08 12:00:00] INFO in app: User-Agent: Mozilla/5.0
[2025-08-08 12:00:00] INFO in app: Requested URL: https://www.youtube.com/watch?v=example
[2025-08-08 12:00:00] INFO in app: Format: best[ext=mp4]/best
[2025-08-08 12:00:01] INFO in app: Starting download for URL: https://www.youtube.com/watch?v=example
[2025-08-08 12:00:01] INFO in app: Format preference: best[ext=mp4]/best
[2025-08-08 12:00:01] INFO in app: Max duration: 7200s, Max size: 500MB
[2025-08-08 12:00:02] INFO in app: Video title: Example Video
[2025-08-08 12:00:02] INFO in app: Video duration: 5:30
[2025-08-08 12:00:02] INFO in app: Video uploader: Example Channel
[2025-08-08 12:00:03] INFO in app: Download progress: 10.5% | Speed: 2.5MB/s | ETA: 00:45
[2025-08-08 12:00:10] INFO in app: Download progress: 50.2% | Speed: 3.1MB/s | ETA: 00:20
[2025-08-08 12:00:30] INFO in app: Download finished, now processing...
[2025-08-08 12:00:31] INFO in app: ✅ DOWNLOAD COMPLETE: /tmp/downloads/a1b2c3d4e5f6.mp4
[2025-08-08 12:00:31] INFO in app: File size: 45.67 MB (47890123 bytes)
[2025-08-08 12:00:31] INFO in app: Video title: Example Video.mp4
[2025-08-08 12:00:31] INFO in app: RESPONSE: Status 200 - Completed in 31.5s
[2025-08-08 12:00:31] INFO in app: ============================================================
```

## Gunicorn Configuration
The Docker container now runs gunicorn with these logging flags:
- `--access-logfile -`: Logs all HTTP access to stdout
- `--error-logfile -`: Logs all errors to stdout
- `--log-level info`: Sets log level to INFO
- `--capture-output`: Captures all Python print/logging output

## Viewing Logs on Render.com

After deploying these changes, you'll be able to see in your Render.com logs:
1. When each request is received with the full URL
2. Download progress with percentage completion
3. Success/failure status with clear indicators
4. Processing time for each request
5. Any errors with full stack traces

The logs will show clear visual separators between requests, making it easy to track individual API calls from start to finish.

## Deployment

To deploy these changes:
1. Commit the changes to your repository
2. Push to the branch connected to Render.com
3. Render will automatically rebuild and deploy with the new logging

After deployment, your logs will show comprehensive information about every API request and download operation.