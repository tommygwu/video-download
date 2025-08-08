# n8n Integration Guide for yt-dlp API

## Overview

This guide explains how to integrate the yt-dlp API deployed on Render.com with n8n workflows for automated video downloading.

## Prerequisites

- yt-dlp API deployed on Render.com
- n8n instance (self-hosted or cloud)
- API key from your Render deployment

## Setup

### 1. Get Your API Endpoint

After deploying to Render.com, your API will be available at:
```
https://yt-dlp-api.onrender.com
```
(Replace `yt-dlp-api` with your actual service name)

### 2. Get Your API Key

1. Go to your Render dashboard
2. Navigate to your yt-dlp-api service
3. Click on "Environment" tab
4. Copy the value of `YT_DLP_API_KEY`

### 3. Create n8n Credentials

1. In n8n, go to **Credentials** → **New**
2. Choose **Header Auth**
3. Configure:
   - **Name**: yt-dlp API
   - **Header Name**: X-API-Key
   - **Header Value**: [Your actual API key value, not the service name]

**Important**: Enter your actual API key value (e.g., `ytdlp_abc123...`), not the Render service name.

## Important: Handling Render.com Free Tier Cold Starts

⚠️ **Critical for Free Tier Users**: Render.com free tier services spin down after 15 minutes of inactivity. The first request after a cold start takes approximately 2 minutes to respond. Your n8n workflow MUST account for this delay.

### Solutions for Cold Start Issues:

1. **Increase Timeout**: Set HTTP Request timeout to at least 180000ms (3 minutes)
2. **Implement Retry Logic**: Use n8n's retry functionality or create a custom retry workflow
3. **Wake-up Strategy**: Send a health check request first to wake the service
4. **Keep-Alive**: Set up a cron job to ping the service every 10 minutes

## Workflow Examples

### Basic Download Workflow (with Cold Start Handling)

```json
{
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "position": [250, 300]
    },
    {
      "name": "Set Video URL",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "video_url",
              "value": "https://www.youtube.com/watch?v=LCEmiRjPEtQ"
            },
            {
              "name": "format",
              "value": "best[ext=mp4]/best"
            }
          ]
        }
      }
    },
    {
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "https://your-service-name.onrender.com/api/download",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonParameters": true,
        "options": {
          "timeout": 180000,
          "retry": {
            "maxTries": 3,
            "waitBetweenTries": 120000
          }
        },
        "bodyParametersJson": "{\n  \"url\": \"{{$json.video_url}}\",\n  \"format\": \"{{$json.format}}\"\n}"
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Set Video URL", "type": "main", "index": 0}]]
    },
    "Set Video URL": {
      "main": [[{"node": "Download Video", "type": "main", "index": 0}]]
    }
  }
}
```

### Wake-Up Strategy Workflow

This workflow first wakes up the Render service before attempting to download:

```json
{
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "position": [250, 300]
    },
    {
      "name": "Wake Up Service",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "method": "GET",
        "url": "https://your-service-name.onrender.com/health",
        "options": {
          "timeout": 180000,
          "ignoreResponseCode": true
        }
      }
    },
    {
      "name": "Wait for Warm Up",
      "type": "n8n-nodes-base.wait",
      "position": [650, 300],
      "parameters": {
        "amount": 10,
        "unit": "seconds"
      }
    },
    {
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300],
      "parameters": {
        "method": "POST",
        "url": "https://your-service-name.onrender.com/api/download",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonParameters": true,
        "options": {
          "timeout": 300000
        },
        "bodyParametersJson": "{\n  \"url\": \"{{$json.video_url}}\",\n  \"format\": \"best[ext=mp4]/best\"\n}"
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Wake Up Service", "type": "main", "index": 0}]]
    },
    "Wake Up Service": {
      "main": [[{"node": "Wait for Warm Up", "type": "main", "index": 0}]]
    },
    "Wait for Warm Up": {
      "main": [[{"node": "Download Video", "type": "main", "index": 0}]]
    }
  }
}
```

### Advanced Workflow with Metadata Check

```json
{
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "position": [250, 300]
    },
    {
      "name": "Get Video Info",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "method": "POST",
        "url": "https://yt-dlp-api.onrender.com/api/info",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "={{$credentials.apiKey}}"
            }
          ]
        },
        "sendBody": true,
        "contentType": "json",
        "bodyParameters": {
          "parameters": [
            {
              "name": "url",
              "value": "={{$json.video_url}}"
            }
          ]
        }
      }
    },
    {
      "name": "Check Duration",
      "type": "n8n-nodes-base.if",
      "position": [650, 300],
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.data.duration}}",
              "operation": "smaller",
              "value2": 7200
            }
          ]
        }
      }
    },
    {
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 250],
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
              "value": "={{$credentials.apiKey}}"
            }
          ]
        },
        "sendBody": true,
        "contentType": "json",
        "bodyParameters": {
          "parameters": [
            {
              "name": "url",
              "value": "={{$node['Get Video Info'].json.data.webpage_url}}"
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
    },
    {
      "name": "Video Too Long",
      "type": "n8n-nodes-base.noOp",
      "position": [850, 400],
      "parameters": {
        "description": "Video exceeds 2 hours"
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Get Video Info", "type": "main", "index": 0}]]
    },
    "Get Video Info": {
      "main": [[{"node": "Check Duration", "type": "main", "index": 0}]]
    },
    "Check Duration": {
      "main": [
        [{"node": "Download Video", "type": "main", "index": 0}],
        [{"node": "Video Too Long", "type": "main", "index": 0}]
      ]
    }
  }
}
```

## API Endpoints

### Health Check
- **GET** `/health`
- No authentication required
- Returns server status and disk usage

### Get Video Info
- **POST** `/api/info`
- Headers: `X-API-Key: your-api-key`
- Body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### Download Video
- **POST** `/api/download`
- Headers: `X-API-Key: your-api-key`
- Body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "best[ext=mp4]/best",  // optional
  "max_duration": 7200  // optional, in seconds
}
```

### Stream Video (Experimental)
- **POST** `/api/stream`
- Headers: `X-API-Key: your-api-key`
- Body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "best[ext=mp4]/best"  // optional
}
```

## n8n HTTP Node Configuration Guide

### Correct Settings for Your HTTP Node:

1. **Parameters Tab:**
   - **Method**: POST
   - **URL**: `https://your-service-name.onrender.com/api/download`
   - **Authentication**: Generic Credential Type
   - **Generic Auth Type**: Header Auth
   - **Header Auth**: Select your created credential (NOT the text "Video Download | Render.com")
   - **Send Body**: ON (enabled)
   - **Body Content Type**: JSON
   - **Specify Body**: Using Fields Below
   - **Body Parameters**:
     - Name: `url`, Value: `{{$json.video_url}}` (or your video URL)
     - Name: `format`, Value: `best[ext=mp4]/best`

2. **Settings Tab:**
   - **Response**:
     - Include Response Headers and Status: ON (for debugging)
     - Never Error: OFF (to see actual errors)
     - Response Format: File
     - Put Output in Field: `data`
   - **Timeout**: `180000` (3 minutes minimum for cold starts)

3. **Add Retry Option** (click "Add option"):
   - Max Tries: 3
   - Wait Between Tries: 120000 (2 minutes)

## Configuration Options

### Environment Variables in n8n

You can set these as environment variables in your n8n workflow:

- `YTDLP_API_URL`: Your Render API URL
- `YTDLP_API_KEY`: Your API key
- `YTDLP_MAX_DURATION`: Maximum video duration in seconds
- `YTDLP_DEFAULT_FORMAT`: Default video format

### Error Handling

Add error handling to your workflows:

1. **HTTP Request Error**: Handle API failures
2. **Timeout**: Set appropriate timeouts (300000ms for 2-hour videos)
3. **File Size**: Check video size before downloading
4. **Rate Limiting**: Add delays between requests

## Best Practices

1. **Check Video Metadata First**
   - Always call `/api/info` before downloading
   - Verify duration and file size

2. **Set Appropriate Timeouts**
   - Use 300000ms (5 minutes) for typical videos
   - Increase for longer videos

3. **Handle Render Free Tier Spin-down**
   - Service spins down after 15 minutes of inactivity
   - First request after spin-down takes ~2 minutes
   - **Solution for n8n**: Add a retry node with 3-minute timeout
   - **Alternative**: Set up a free cron job to ping `/health` every 10 minutes
   - **Note**: This is perfect for your "few videos daily" use case

4. **Implement Retry Logic**
   - Add retry nodes for failed downloads
   - Use exponential backoff

5. **Monitor Disk Usage**
   - Check `/health` endpoint regularly
   - Clean up downloaded files after processing

## Troubleshooting

### Common Issues

1. **503 Service Unavailable / "Service unavailable - try again later"**
   - **Cause**: Render.com free tier service is cold (spun down)
   - **Solution 1**: Set HTTP timeout to 180000ms (3 minutes) minimum
   - **Solution 2**: Enable retry with 3 attempts and 120000ms between tries
   - **Solution 3**: Use wake-up strategy workflow (see example above)
   - **Prevention**: Set up external cron job to ping `/health` every 10 minutes

2. **401 Unauthorized**
   - Check your API key value (not service name)
   - Ensure X-API-Key header is set correctly
   - Verify credentials in n8n match Render environment variable

3. **Timeout Errors (even with high timeout)**
   - Service might need more than 2 minutes to start
   - Try timeout of 300000ms (5 minutes)
   - Check Render dashboard for deployment status
   - Consider upgrading to paid tier for always-on service

4. **"Never Error" masking real issues**
   - Disable "Never Error" option in HTTP node
   - Enable "Include Response Headers and Status"
   - Check actual error messages in response

5. **413 File Too Large**
   - Video exceeds MAX_DOWNLOAD_SIZE_MB
   - Check video size with `/api/info` first
   - Adjust MAX_DOWNLOAD_SIZE_MB in Render environment

6. **No Response / Connection Failed**
   - Check if service is deployed on Render
   - Verify URL is correct (check for typos)
   - Ensure service hasn't been suspended (check Render dashboard)
   - Check Render logs for deployment errors

### Debugging

1. Check Render logs:
   ```bash
   render logs yt-dlp-api --tail
   ```

2. Test with curl:
   ```bash
   curl -X POST https://yt-dlp-api.onrender.com/api/info \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
   ```

3. Monitor health:
   ```bash
   curl https://yt-dlp-api.onrender.com/health
   ```

## Example Use Cases

### 1. Daily Video Archive
- Schedule workflow to run daily
- Download specific channel videos
- Store in cloud storage

### 2. Video Processing Pipeline
- Download video
- Extract audio
- Transcribe with Whisper
- Store transcript

### 3. Content Monitoring
- Monitor playlist for new videos
- Download when detected
- Send notification

## Security Considerations

1. **Never expose your API key** in public workflows
2. **Use n8n credentials** for API key storage
3. **Implement rate limiting** to prevent abuse
4. **Monitor usage** via Render dashboard
5. **Rotate API keys** regularly

## Support

For issues with:
- **yt-dlp API**: Check this repository's issues
- **Render deployment**: Contact Render support
- **n8n workflows**: Visit n8n community forum