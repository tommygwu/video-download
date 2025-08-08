# yt-dlp API Documentation

## Overview

REST API wrapper for yt-dlp, designed for deployment on Render.com to enable video downloading through HTTP endpoints.

## Base URL

```
https://your-service-name.onrender.com
```

## Authentication

All API endpoints (except `/health`) require authentication via API key.

### Headers

```
X-API-Key: your-api-key-here
```

## Endpoints

### Health Check

Check if the service is running and get system information.

**Endpoint:** `GET /health`

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T18:17:45.094940",
  "free_disk_mb": 1019900.98,
  "download_dir": "/tmp/downloads",
  "version": "1.0.0"
}
```

### Get Video Information

Retrieve metadata about a video without downloading it.

**Endpoint:** `POST /api/info`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Video Title",
    "duration": 2371,
    "duration_string": "39:31",
    "thumbnail": "https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg",
    "uploader": "Channel Name",
    "upload_date": "20250619",
    "view_count": 1872654,
    "like_count": 49369,
    "description": "Video description (first 500 characters)...",
    "webpage_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "extractor": "youtube",
    "formats_available": 20,
    "filesize_approx": 76171697
  }
}
```

### Download Video

Download a video and return it as a file attachment.

**Endpoint:** `POST /api/download`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "best[ext=mp4]/best",  // optional, default: "best[ext=mp4]/best"
  "max_duration": 7200  // optional, in seconds, default: 7200 (2 hours)
}
```

**Response:**
- Success: Binary file stream with appropriate MIME type
- Error: JSON error response

**Response Headers:**
```
Content-Type: video/mp4
Content-Disposition: attachment; filename="Video Title.mp4"
```

### Stream Video (Experimental)

Stream a video download for large files without saving to disk first.

**Endpoint:** `POST /api/stream`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "best[ext=mp4]/best"  // optional
}
```

**Response:**
- Chunked transfer encoding
- Streams video data as it downloads

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "message": "URL is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

### 413 Request Entity Too Large
```json
{
  "error": "File too large",
  "message": "Maximum file size is 500MB"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal error",
  "message": "An unexpected error occurred"
}
```

## Format Selection

The `format` parameter uses yt-dlp's format selection syntax:

- `best`: Best quality format
- `worst`: Worst quality format
- `best[ext=mp4]`: Best MP4 format
- `best[height<=720]`: Best format up to 720p
- `best[filesize<100M]`: Best format under 100MB

See [yt-dlp format selection](https://github.com/yt-dlp/yt-dlp#format-selection) for more options.

## Rate Limiting

- Default: 10 requests per minute per API key
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable

## Timeouts

- Default request timeout: 300 seconds (5 minutes)
- Configurable in client applications
- Recommended settings:
  - Short videos (<10 min): 60 seconds
  - Medium videos (10-30 min): 180 seconds
  - Long videos (30-120 min): 300 seconds

## Environment Variables

Configure the API behavior with these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `YT_DLP_API_KEY` | `change-me-in-production` | API authentication key |
| `MAX_DOWNLOAD_SIZE_MB` | `500` | Maximum file size in MB |
| `MAX_FILE_AGE_MINUTES` | `30` | Time before cleaning up downloaded files |
| `DOWNLOAD_DIR` | `/tmp/downloads` | Directory for temporary downloads |
| `PORT` | `5000` | Server port |
| `FLASK_ENV` | `production` | Flask environment |

## cURL Examples

### Get Video Info
```bash
curl -X POST https://your-api.onrender.com/api/info \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

### Download Video
```bash
curl -X POST https://your-api.onrender.com/api/download \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}' \
  -o video.mp4
```

### Check Health
```bash
curl https://your-api.onrender.com/health
```

## Python Example

```python
import requests

API_URL = "https://your-api.onrender.com"
API_KEY = "your-api-key"

# Get video info
response = requests.post(
    f"{API_URL}/api/info",
    headers={"X-API-Key": API_KEY},
    json={"url": "https://www.youtube.com/watch?v=VIDEO_ID"}
)
info = response.json()
print(f"Title: {info['data']['title']}")
print(f"Duration: {info['data']['duration_string']}")

# Download video
response = requests.post(
    f"{API_URL}/api/download",
    headers={"X-API-Key": API_KEY},
    json={"url": "https://www.youtube.com/watch?v=VIDEO_ID"},
    stream=True
)

with open("video.mp4", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');
const fs = require('fs');

const API_URL = 'https://your-api.onrender.com';
const API_KEY = 'your-api-key';

// Get video info
async function getVideoInfo(url) {
  const response = await axios.post(
    `${API_URL}/api/info`,
    { url },
    { headers: { 'X-API-Key': API_KEY } }
  );
  return response.data;
}

// Download video
async function downloadVideo(url, outputPath) {
  const response = await axios.post(
    `${API_URL}/api/download`,
    { url },
    {
      headers: { 'X-API-Key': API_KEY },
      responseType: 'stream'
    }
  );
  
  const writer = fs.createWriteStream(outputPath);
  response.data.pipe(writer);
  
  return new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
}
```

## Deployment

### Render.com Deployment

1. Push code to GitHub
2. Connect repository to Render
3. Deploy using `render.yaml` configuration
4. Set environment variables in Render dashboard

### Docker Deployment

```bash
# Build image
docker build -f deploy/Dockerfile -t yt-dlp-api .

# Run locally
docker run -p 5000:5000 \
  -e YT_DLP_API_KEY=your-api-key \
  yt-dlp-api
```

## Limitations

1. **File Size**: Maximum 500MB per download (configurable)
2. **Duration**: Maximum 2 hours per video (configurable)
3. **Concurrent Downloads**: Limited by server resources
4. **Temporary Storage**: Files are deleted after 30 minutes
5. **Format Support**: Depends on yt-dlp and FFmpeg capabilities

## Security

1. **API Key**: Always use HTTPS in production
2. **Input Validation**: URLs are validated before processing
3. **File Cleanup**: Automatic cleanup prevents disk space issues
4. **Rate Limiting**: Prevents abuse and resource exhaustion
5. **No Logging**: Video URLs and content are not logged

## Troubleshooting

### Service Spins Down (Free Tier)
- First request after 15 minutes takes ~2 minutes
- Solution: Implement health check cron job

### Download Fails
- Check video availability
- Verify format compatibility
- Check file size limits

### Timeout Errors
- Increase client timeout
- Use streaming endpoint for large files
- Check network connectivity

## License

This API wrapper follows the same license as yt-dlp (Unlicense).