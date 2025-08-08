# yt-dlp API for Render.com

A Flask-based REST API wrapper for yt-dlp, designed for deployment on Render.com to enable video downloading through HTTP endpoints.

## Features

✅ **Download videos directly** on the server (solves IP restriction issues)  
✅ **Stream large files** without saving to disk  
✅ **Get video metadata** before downloading  
✅ **API key authentication** for security  
✅ **Automatic file cleanup** to manage storage  
✅ **Docker support** for easy deployment  
✅ **n8n integration** ready  

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r api/requirements.txt
```

2. Set environment variables:
```bash
export YT_DLP_API_KEY=your-test-key
export FLASK_ENV=development
```

3. Run the server:
```bash
python api/app.py
```

4. Test the API:
```bash
# Health check
curl http://localhost:5000/health

# Get video info
curl -X POST http://localhost:5000/api/info \
  -H "X-API-Key: your-test-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

### Deploy to Render.com

1. Push to GitHub:
```bash
git add .
git commit -m "Add yt-dlp API for Render deployment"
git push origin main
```

2. Deploy on Render:
   - Go to [render.com](https://render.com)
   - Create new **Web Service**
   - Connect your GitHub repository
   - Choose **Docker** environment
   - Render will auto-detect `render.yaml`
   - Click **Create Web Service**

3. Configure environment:
   - Go to **Environment** tab
   - `YT_DLP_API_KEY` will be auto-generated
   - Adjust other settings as needed

4. Get your API URL:
   - Format: `https://your-service-name.onrender.com`
   - Test: `curl https://your-service-name.onrender.com/health`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth) |
| `/api/info` | POST | Get video metadata |
| `/api/download` | POST | Download video |
| `/api/stream` | POST | Stream video (experimental) |

See [API Documentation](../docs/API.md) for full details.

## n8n Integration

See [n8n Setup Guide](../docs/N8N_SETUP.md) for workflow examples.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YT_DLP_API_KEY` | (generated) | API authentication key |
| `MAX_DOWNLOAD_SIZE_MB` | `500` | Maximum file size |
| `MAX_FILE_AGE_MINUTES` | `30` | Cleanup delay |
| `DOWNLOAD_DIR` | `/tmp/downloads` | Download directory |

### Render.com Settings

**Free Tier:**
- 750 hours/month
- Spins down after 15 minutes
- 2-minute spin-up time
- No persistent disk

**Starter Tier ($7/month):**
- Always on
- 10GB persistent disk available
- Better for production use

## Project Structure

```
api/
├── app.py           # Main Flask application
├── config.py        # Configuration management
├── requirements.txt # Python dependencies
└── README.md        # This file

deploy/
├── Dockerfile       # Docker configuration
├── .dockerignore    # Docker ignore rules
└── render.yaml      # Render deployment config
```

## Testing

Test with the sample video:
```bash
# Short video (19 seconds)
curl -X POST http://localhost:5000/api/download \
  -H "X-API-Key: your-test-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}' \
  -o test.mp4

# Target video (40 minutes)
curl -X POST http://localhost:5000/api/info \
  -H "X-API-Key: your-test-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=LCEmiRjPEtQ"}'
```

## Docker

Build and run locally:
```bash
# Build
docker build -f deploy/Dockerfile -t yt-dlp-api .

# Run
docker run -p 5000:5000 \
  -e YT_DLP_API_KEY=test-key \
  yt-dlp-api

# Test
curl http://localhost:5000/health
```

## Troubleshooting

### Service Spins Down
- Free tier spins down after 15 minutes
- First request takes ~2 minutes
- Solution: Set up health check cron job

### Download Failures
- Check video availability
- Verify file size < MAX_DOWNLOAD_SIZE_MB
- Check duration < 2 hours
- Review Render logs

### Timeout Errors
- Increase client timeout (300s recommended)
- Use `/api/stream` for large files
- Check Render service status

## Monitoring

Check logs:
```bash
# Via Render CLI
render logs your-service-name --tail

# Via Dashboard
# Go to your service → Logs tab
```

Monitor health:
```bash
watch -n 60 'curl -s https://your-api.onrender.com/health | jq'
```

## Security Notes

1. **Always use HTTPS** in production
2. **Rotate API keys** regularly
3. **Monitor usage** for abuse
4. **Set rate limits** appropriately
5. **Don't log video URLs** or content

## Upstream Syncing

This implementation is designed to minimize merge conflicts:

1. All API code is in `api/` directory
2. Deployment configs in `deploy/`
3. Documentation in `docs/`

To sync with upstream yt-dlp:
```bash
git fetch upstream
git merge upstream/master --no-ff
# Resolve any conflicts (unlikely in our directories)
git push origin main
```

## License

Follows yt-dlp license (Unlicense)