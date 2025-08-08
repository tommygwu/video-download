# Deployment Guide for yt-dlp API on Render.com

## Prerequisites

- GitHub account
- Render.com account
- This repository forked/cloned to your GitHub

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/video-download.git
cd video-download

# Ensure API files are present
ls -la api/
ls -la deploy/

# Commit any changes
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Deploy to Render.com

#### Option A: Using render.yaml (Recommended)

1. Go to [render.com/dashboard](https://dashboard.render.com)
2. Click **New +** → **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml`
5. Review settings and click **Apply**

#### Option B: Manual Setup

1. Go to [render.com/dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect GitHub and select your repository
4. Configure:
   - **Name**: `yt-dlp-api` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `./deploy/Dockerfile`
   - **Docker Context Directory**: `.` (repository root)
5. Click **Create Web Service**

### 3. Configure Environment Variables

In Render Dashboard → Your Service → **Environment**:

| Variable | Value | Notes |
|----------|-------|-------|
| `YT_DLP_API_KEY` | Click "Generate" | Save this key! |
| `MAX_DOWNLOAD_SIZE_MB` | `500` | Adjust as needed |
| `MAX_FILE_AGE_MINUTES` | `30` | Cleanup delay |
| `FLASK_ENV` | `production` | For production |

### 4. Choose Service Plan

#### Free Tier (Recommended to Start)
- **Cost**: $0/month
- **Limits**: 
  - 750 hours/month (plenty for a few videos daily)
  - Spins down after 15 minutes of inactivity
  - Takes ~2 minutes to spin back up
  - No persistent disk (uses `/tmp` only)
  - 100GB bandwidth/month
- **Perfect for**: Your use case (1-2 hour videos, few downloads daily)
- **Note**: Videos are downloaded to `/tmp` and streamed immediately, no long-term storage needed

#### Starter Tier (Optional Upgrade)
- **Cost**: $7/month
- **Benefits**:
  - Always on (no spin-down delay)
  - 10GB persistent disk option
  - Better for high-frequency use
- **Consider if**: You need instant response times or >10 downloads/day

To upgrade:
1. Go to service **Settings**
2. Under **Instance Type**, select **Starter**
3. Click **Save Changes**

### 5. Add Persistent Disk (Optional, Paid Only)

If using Starter plan:
1. Go to **Disks** tab
2. Click **Add Disk**
3. Configure:
   - **Name**: `downloads`
   - **Mount Path**: `/data`
   - **Size**: `10 GB`
4. Update environment variable:
   - `DOWNLOAD_DIR`: `/data/downloads`

### 6. Verify Deployment

Wait for deployment (5-10 minutes), then test:

```bash
# Check health
curl https://yt-dlp-api.onrender.com/health

# Test API (replace with your URL and API key)
curl -X POST https://yt-dlp-api.onrender.com/api/info \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

### 7. Set Up Auto-Deploy (Optional)

1. In Render Dashboard → Your Service
2. Go to **Settings** → **Build & Deploy**
3. Enable **Auto-Deploy**: `Yes`
4. Now pushes to GitHub auto-deploy

### 8. Configure Health Checks

Render automatically configures health checks from `render.yaml`.

To modify:
1. Go to **Settings** → **Health & Alerts**
2. Health Check Path: `/health`
3. Check Interval: `300 seconds`

### 9. Prevent Spin-Down (Free Tier)

To keep free service active:

#### Option A: External Cron Service
Use [cron-job.org](https://cron-job.org):
1. Create account
2. Add job:
   - URL: `https://yt-dlp-api.onrender.com/health`
   - Schedule: Every 10 minutes
   - Method: GET

#### Option B: n8n Schedule
In your n8n instance:
1. Create workflow with Schedule trigger
2. Every 10 minutes
3. HTTP Request to `/health`

### 10. Monitor Your Service

#### View Logs
```bash
# In Render Dashboard
Service → Logs tab

# Real-time logs
Service → Logs → "Live tail"
```

#### Check Metrics
Service → **Metrics** tab shows:
- CPU usage
- Memory usage
- Network I/O
- Disk usage

## Troubleshooting Deployment

### Build Fails

Check Dockerfile syntax:
```bash
docker build -f deploy/Dockerfile -t test .
```

Common issues:
- Missing files in repository
- Python version mismatch
- FFmpeg installation failure

### Service Won't Start

Check logs for errors:
- Port binding issues
- Missing environment variables
- Python import errors

### Health Check Fails

Verify locally:
```bash
python api/app.py
curl http://localhost:5000/health
```

### Slow First Request

Normal for free tier:
- Service spins down after 15 minutes
- Takes 2 minutes to spin up
- Solution: Use health check cron

## Production Checklist

- [ ] Set strong `YT_DLP_API_KEY`
- [ ] Configure `MAX_DOWNLOAD_SIZE_MB` appropriately
- [ ] Set up monitoring/alerts
- [ ] Configure auto-deploy
- [ ] Set up health check cron (free tier)
- [ ] Document API key for n8n
- [ ] Test with actual workload
- [ ] Monitor disk usage
- [ ] Set up log aggregation (optional)

## Updating the Service

### Manual Deploy
```bash
git pull origin main
git push origin main
# Click "Manual Deploy" in Render
```

### Auto-Deploy
```bash
git pull origin main
git push origin main
# Deploys automatically
```

### Update Environment Variables
1. Dashboard → Environment
2. Update values
3. Service auto-restarts

## Rollback Deployment

If issues occur:
1. Go to **Events** tab
2. Find previous successful deploy
3. Click **Rollback to this deploy**

## Cost Optimization

### Monitor Usage
- Check **Metrics** tab regularly
- Watch bandwidth usage (100GB free limit)
- Monitor compute hours

### Optimize Settings
- Reduce `MAX_DOWNLOAD_SIZE_MB` if needed
- Decrease `MAX_FILE_AGE_MINUTES` for faster cleanup
- Use format selection to limit quality

### Scale Down When Idle
- Switch to free tier during development
- Pause service when not in use
- Use manual deploy instead of auto

## Security Best Practices

1. **Rotate API Keys Monthly**
   - Generate new key in Environment
   - Update n8n workflows
   - Delete old key

2. **Monitor Access Logs**
   - Check for unusual patterns
   - Look for repeated 401 errors
   - Watch for large downloads

3. **Set Up Alerts**
   - High CPU usage
   - Disk space warnings
   - Failed health checks

4. **Restrict Access**
   - Use IP allowlisting if possible
   - Implement rate limiting
   - Monitor for abuse

## Next Steps

1. **Test with n8n**: See [N8N_SETUP.md](./N8N_SETUP.md)
2. **Monitor Performance**: Check metrics after first day
3. **Optimize**: Adjust settings based on usage
4. **Scale**: Upgrade plan if needed

## Support

- **Render Issues**: [Render Community](https://community.render.com)
- **API Issues**: Check repository issues
- **yt-dlp Issues**: [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)

## Quick Commands Reference

```bash
# Check service status
curl https://your-api.onrender.com/health

# View logs (Render CLI)
render logs your-service --tail

# Test download
curl -X POST https://your-api.onrender.com/api/download \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "VIDEO_URL"}' \
  -o video.mp4

# Get video info
curl -X POST https://your-api.onrender.com/api/info \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "VIDEO_URL"}' | jq
```