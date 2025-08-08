# Plan: yt-dlp API Implementation on Render.com

## Executive Summary
Deploy yt-dlp as a full-featured API on Render.com that directly downloads videos and returns them to n8n, solving the IP restriction issue that makes Vercel unsuitable for this use case.

## Why Render.com Instead of Vercel

### The IP Restriction Problem
- **Vercel extracts URL** → URL locked to Vercel's IP
- **n8n tries to download** → YouTube returns 403 Forbidden
- **Result**: Downloads fail due to IP mismatch

### Render.com Advantages
- **100-minute timeout** (vs Vercel's 10-60 seconds)
- **No response size limits** (vs Vercel's 50MB)
- **Docker support** for full yt-dlp + FFmpeg
- **Persistent storage** for temporary files
- **Background workers** for async processing
- **Free tier**: 750 hours/month

## Architecture Design

### Direct Download API
The API will:
1. Receive video URL from n8n
2. Download video on Render server (same IP for extraction & download)
3. Stream file back to n8n or provide temporary download link
4. Clean up temporary files after transfer

## Implementation Plan

### Phase 1: Create Flask API Application

#### 1.1 Main Application (`app.py`)
```python
from flask import Flask, request, jsonify, send_file, Response
import yt_dlp
import os
import tempfile
import hashlib
import time
from datetime import datetime, timedelta
import threading
import shutil

app = Flask(__name__)

# Configuration
DOWNLOAD_DIR = '/tmp/downloads'
MAX_FILE_AGE_MINUTES = 30
API_KEY = os.environ.get('YT_DLP_API_KEY', 'change-me-in-production')
MAX_DOWNLOAD_SIZE_MB = int(os.environ.get('MAX_DOWNLOAD_SIZE_MB', '500'))

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
```

#### 1.2 Authentication Middleware
```python
def require_api_key(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

#### 1.3 Video Download Endpoint
```python
@app.route('/api/download', methods=['POST'])
@require_api_key
def download_video():
    """
    Download video and return it directly
    """
    data = request.json
    url = data.get('url')
    format_preference = data.get('format', 'best[ext=mp4]/best')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate unique filename
    video_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()
    output_path = os.path.join(DOWNLOAD_DIR, f'{video_id}.%(ext)s')
    
    # yt-dlp options
    ydl_opts = {
        'outtmpl': output_path,
        'format': format_preference,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': MAX_DOWNLOAD_SIZE_MB * 1024 * 1024,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
    }
    
    try:
        # Extract info first
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            downloaded_file = output_path.replace('%(ext)s', info['ext'])
            
            if not os.path.exists(downloaded_file):
                return jsonify({'error': 'Download failed'}), 500
            
            # Return file
            return send_file(
                downloaded_file,
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.{info['ext']}",
                mimetype='video/mp4' if info['ext'] == 'mp4' else 'application/octet-stream'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Schedule cleanup
        threading.Timer(60, cleanup_file, [downloaded_file]).start()
```

#### 1.4 Metadata Extraction Endpoint
```python
@app.route('/api/info', methods=['POST'])
@require_api_key
def get_video_info():
    """
    Get video metadata without downloading
    """
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'success': True,
                'data': {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'formats': len(info.get('formats', [])),
                    'filesize_approx': info.get('filesize_approx'),
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### 1.5 Stream Download Endpoint (Alternative)
```python
@app.route('/api/stream', methods=['POST'])
@require_api_key
def stream_video():
    """
    Stream video download for large files
    """
    data = request.json
    url = data.get('url')
    
    def generate():
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'outtmpl': '-',  # Output to stdout
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # This would need custom implementation to stream
            # For now, this is a placeholder
            yield b'Streaming not yet implemented'
    
    return Response(generate(), mimetype='video/mp4')
```

#### 1.6 Cleanup Functions
```python
def cleanup_file(filepath):
    """Remove file after delay"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass

def cleanup_old_files():
    """Remove files older than MAX_FILE_AGE_MINUTES"""
    while True:
        time.sleep(300)  # Check every 5 minutes
        cutoff_time = time.time() - (MAX_FILE_AGE_MINUTES * 60)
        
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.getctime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                except:
                    pass

# Start cleanup thread
threading.Thread(target=cleanup_old_files, daemon=True).start()
```

### Phase 2: Docker Configuration

#### 2.1 Create `Dockerfile`
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create download directory
RUN mkdir -p /tmp/downloads

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "2", "app:app"]
```

#### 2.2 Create `requirements.txt`
```
Flask==3.0.0
yt-dlp==2024.7.16
gunicorn==21.2.0
```

### Phase 3: Render Configuration

#### 3.1 Create `render.yaml`
```yaml
services:
  - type: web
    name: yt-dlp-api
    runtime: docker
    plan: free  # or "starter" for $7/month
    dockerfilePath: ./Dockerfile
    envVars:
      - key: YT_DLP_API_KEY
        generateValue: true  # Auto-generate secure key
      - key: MAX_DOWNLOAD_SIZE_MB
        value: 500
    disk:
      name: downloads
      mountPath: /tmp/downloads
      sizeGB: 10  # Temporary storage for downloads
```

#### 3.2 Alternative: Direct Python Service
```yaml
services:
  - type: web
    name: yt-dlp-api
    runtime: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app:app"
    envVars:
      - key: YT_DLP_API_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Phase 4: n8n Integration

#### 4.1 n8n Workflow for Direct Download
```json
{
  "nodes": [
    {
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://yt-dlp-api.onrender.com/api/download",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "={{ $credentials.apiKey }}"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "url",
              "value": "={{ $json.youtube_url }}"
            },
            {
              "name": "format",
              "value": "best[ext=mp4]/best"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          },
          "timeout": 300000
        }
      }
    }
  ]
}
```

#### 4.2 n8n Workflow with Metadata Check
```json
{
  "nodes": [
    {
      "name": "Get Video Info",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://yt-dlp-api.onrender.com/api/info",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "your-api-key"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "url",
              "value": "={{ $json.youtube_url }}"
            }
          ]
        }
      }
    },
    {
      "name": "Check File Size",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.data.filesize_approx }}",
              "operation": "smaller",
              "value2": 524288000
            }
          ]
        }
      }
    },
    {
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://yt-dlp-api.onrender.com/api/download",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "your-api-key"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "url",
              "value": "={{ $node['Get Video Info'].json.data.webpage_url }}"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          },
          "timeout": 300000
        }
      }
    }
  ]
}
```

## Deployment Steps

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export YT_DLP_API_KEY=test-key
python app.py

# Test
curl -X POST http://localhost:5000/api/info \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### 2. Deploy to Render
```bash
# Install Render CLI (optional)
brew tap render-oss/render
brew install render

# Or use web dashboard
# 1. Connect GitHub repo
# 2. Create new Web Service
# 3. Select Docker or Python environment
# 4. Set environment variables
# 5. Deploy
```

### 3. Configure n8n
1. Add API endpoint URL
2. Set API key in n8n credentials
3. Configure timeout for large downloads
4. Test with sample video

## Cost Analysis

### Render.com Free Tier
- **750 hours/month** of compute
- **100GB bandwidth**
- **Spins down after 15 minutes** of inactivity
- Perfect for "handful of downloads daily"

### Render.com Starter ($7/month)
- **Always-on service**
- **No spin-down delays**
- **Better for production use**

### Comparison with Alternatives
| Solution | Cost | Timeout | Storage | Complexity |
|----------|------|---------|---------|------------|
| Render.com Free | $0 | 100 min | 10GB disk | Medium |
| Render.com Paid | $7/mo | 100 min | 10GB+ disk | Medium |
| Vercel | $0-20 | 60 sec | 50MB response | High (IP issues) |
| VPS | $5-10/mo | Unlimited | 25GB+ | Low |
| n8n Direct | $0 | Unlimited | Local | Lowest |

## Security Considerations

### API Security
- **API Key Authentication**: Required for all endpoints
- **Rate Limiting**: Implement per-key limits
- **Input Validation**: Sanitize URLs, check domains
- **File Size Limits**: Prevent abuse with MAX_DOWNLOAD_SIZE_MB

### Data Protection
- **Automatic Cleanup**: Remove files after 30 minutes
- **No Permanent Storage**: All downloads are temporary
- **HTTPS Only**: Enforce encrypted connections
- **No Logging**: Don't log video URLs or content

## Monitoring & Maintenance

### Health Checks
```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'disk_usage': shutil.disk_usage(DOWNLOAD_DIR).used
    })
```

### Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log downloads without URLs for privacy
logger.info(f"Download completed: {info.get('duration')}s video")
```

## Limitations & Solutions

### Current Limitations
1. **File Size**: Limited by available disk space
2. **Concurrent Downloads**: Limited by server resources
3. **Bandwidth**: Subject to Render's limits

### Future Enhancements
1. **Queue System**: Add Redis for job queuing
2. **CDN Integration**: Upload to S3/CloudFlare for serving
3. **Webhook Support**: Notify n8n when download completes
4. **Format Conversion**: Add FFmpeg processing options

## Conclusion

This Render.com implementation solves the critical IP restriction issue by:
- **Downloading directly on the API server** (same IP for extraction and download)
- **Streaming files back to n8n** (no URL expiration issues)
- **Providing generous timeouts** (100 minutes vs Vercel's 60 seconds)
- **Supporting large files** (no 50MB response limit)

For your use case of "handful of downloads daily via n8n", this solution provides:
- ✅ **Reliable downloads** without IP restrictions
- ✅ **Simple n8n integration** with HTTP Request node
- ✅ **Cost-effective** with free tier or $7/month
- ✅ **Full yt-dlp features** including format selection
- ✅ **Automatic cleanup** to manage storage