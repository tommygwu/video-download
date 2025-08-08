#!/usr/bin/env python3
"""
yt-dlp API Server for Render.com deployment
Provides REST API endpoints for downloading videos via yt-dlp
"""

import os
import sys
import json
import hashlib
import time
import tempfile
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import yt_dlp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from werkzeug.exceptions import RequestEntityTooLarge
import yt_dlp

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
app.logger.setLevel(logging.INFO)

# Configuration
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/tmp/downloads')
MAX_FILE_AGE_MINUTES = int(os.environ.get('MAX_FILE_AGE_MINUTES', '30'))
API_KEY = os.environ.get('YT_DLP_API_KEY', 'change-me-in-production')
MAX_DOWNLOAD_SIZE_MB = int(os.environ.get('MAX_DOWNLOAD_SIZE_MB', '500'))
MAX_CONTENT_LENGTH = MAX_DOWNLOAD_SIZE_MB * 1024 * 1024

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure download directory exists
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Cleanup thread management
cleanup_thread = None

def log_request(f):
    """Decorator to log incoming requests"""
    def decorated_function(*args, **kwargs):
        # Log request details
        app.logger.info(f"{'='*60}")
        app.logger.info(f"REQUEST RECEIVED: {request.method} {request.path}")
        app.logger.info(f"Client IP: {request.remote_addr}")
        app.logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
        
        # Log request body for POST requests
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
            if data and 'url' in data:
                app.logger.info(f"Requested URL: {data['url']}")
                app.logger.info(f"Format: {data.get('format', 'default')}")
        
        start_time = time.time()
        
        try:
            # Execute the actual function
            result = f(*args, **kwargs)
            
            # Log response details
            elapsed_time = time.time() - start_time
            status_code = result[1] if isinstance(result, tuple) else 200
            app.logger.info(f"RESPONSE: Status {status_code} - Completed in {elapsed_time:.2f}s")
            app.logger.info(f"{'='*60}")
            
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            app.logger.error(f"REQUEST FAILED: {str(e)} - Failed after {elapsed_time:.2f}s")
            app.logger.info(f"{'='*60}")
            raise
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_api_key(f):
    """Decorator for API key authentication"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def cleanup_file(filepath, delay=60):
    """Remove file after delay"""
    def remove():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                app.logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            app.logger.error(f"Error cleaning up file {filepath}: {e}")
    
    timer = threading.Timer(delay, remove)
    timer.daemon = True
    timer.start()

def cleanup_old_files():
    """Remove files older than MAX_FILE_AGE_MINUTES"""
    while True:
        try:
            time.sleep(300)  # Check every 5 minutes
            cutoff_time = time.time() - (MAX_FILE_AGE_MINUTES * 60)
            
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath) and os.path.getctime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        app.logger.info(f"Removed old file: {filepath}")
                    except Exception as e:
                        app.logger.error(f"Error removing old file {filepath}: {e}")
        except Exception as e:
            app.logger.error(f"Error in cleanup thread: {e}")

@app.route('/health', methods=['GET'])
@log_request
def health_check():
    """Health check endpoint for monitoring"""
    try:
        disk_usage = os.statvfs(DOWNLOAD_DIR)
        free_space_mb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024 * 1024)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'free_disk_mb': round(free_space_mb, 2),
            'download_dir': DOWNLOAD_DIR,
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/info', methods=['POST'])
@require_api_key
@log_request
def get_video_info():
    """Get video metadata without downloading"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request', 'message': 'Request body must be JSON'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Missing parameter', 'message': 'URL is required'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant metadata
            metadata = {
                'success': True,
                'data': {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'duration_string': info.get('duration_string'),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'description': info.get('description', '')[:500],  # Limit description length
                    'webpage_url': info.get('webpage_url'),
                    'extractor': info.get('extractor'),
                    'formats_available': len(info.get('formats', [])),
                    'filesize_approx': info.get('filesize_approx'),
                }
            }
            
            # Try to get best format filesize
            if info.get('formats'):
                best_format = max(
                    (f for f in info['formats'] if f.get('filesize')),
                    key=lambda x: x.get('filesize', 0),
                    default=None
                )
                if best_format:
                    metadata['data']['filesize_approx'] = best_format.get('filesize')
            
            return jsonify(metadata)
            
    except yt_dlp.utils.DownloadError as e:
        return jsonify({
            'success': False,
            'error': 'Download error',
            'message': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f"Error in get_video_info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal error',
            'message': str(e)
        }), 500

@app.route('/api/download', methods=['POST'])
@require_api_key
@log_request
def download_video():
    """Download video and return it directly"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request', 'message': 'Request body must be JSON'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Missing parameter', 'message': 'URL is required'}), 400
        
        format_preference = data.get('format', 'best[ext=mp4]/best')
        max_duration = data.get('max_duration', 7200)  # Default 2 hours
        
        # Generate unique filename
        video_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:12]
        output_template = os.path.join(DOWNLOAD_DIR, f'{video_id}.%(ext)s')
        
        # Progress tracking function
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                app.logger.info(f"Download progress: {percent} | Speed: {speed} | ETA: {eta}")
            elif d['status'] == 'finished':
                app.logger.info(f"Download finished, now processing...")
            elif d['status'] == 'error':
                app.logger.error(f"Download error: {d.get('error', 'Unknown error')}")
        
        # yt-dlp options
        ydl_opts = {
            'outtmpl': output_template,
            'format': format_preference,
            'quiet': False,  # Enable output for better logging
            'no_warnings': False,
            'noplaylist': True,
            'max_filesize': MAX_DOWNLOAD_SIZE_MB * 1024 * 1024,
            'match_filter': lambda info: None if info.get('duration', 0) <= max_duration else 'Video too long',
            'progress_hooks': [progress_hook],
            'logger': app.logger,  # Use Flask's logger
        }
        
        # Download the video
        app.logger.info(f"Starting download for URL: {url}")
        app.logger.info(f"Format preference: {format_preference}")
        app.logger.info(f"Max duration: {max_duration}s, Max size: {MAX_DOWNLOAD_SIZE_MB}MB")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Log extracted video info
            app.logger.info(f"Video title: {info.get('title', 'Unknown')}")
            app.logger.info(f"Video duration: {info.get('duration_string', 'Unknown')}")
            app.logger.info(f"Video uploader: {info.get('uploader', 'Unknown')}")
            
            # Find the downloaded file
            ext = info.get('ext', 'mp4')
            downloaded_file = output_template.replace('%(ext)s', ext)
            
            if not os.path.exists(downloaded_file):
                app.logger.warning(f"File not found at expected path: {downloaded_file}")
                # Try to find file with different extension
                for file in os.listdir(DOWNLOAD_DIR):
                    if file.startswith(video_id):
                        downloaded_file = os.path.join(DOWNLOAD_DIR, file)
                        app.logger.info(f"Found file at: {downloaded_file}")
                        break
            
            if not os.path.exists(downloaded_file):
                app.logger.error(f"Downloaded file not found! Video ID: {video_id}")
                return jsonify({
                    'success': False,
                    'error': 'Download failed',
                    'message': 'File not found after download'
                }), 500
            
            file_size = os.path.getsize(downloaded_file)
            file_size_mb = file_size / (1024 * 1024)
            app.logger.info(f"✅ DOWNLOAD COMPLETE: {downloaded_file}")
            app.logger.info(f"File size: {file_size_mb:.2f} MB ({file_size} bytes)")
            app.logger.info(f"Video title: {info.get('title', 'video')}.{ext}")
            
            # Schedule cleanup after response
            cleanup_file(downloaded_file, delay=120)
            
            # Return the file
            return send_file(
                downloaded_file,
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.{ext}",
                mimetype='video/mp4' if ext == 'mp4' else 'application/octet-stream'
            )
            
    except yt_dlp.utils.DownloadError as e:
        app.logger.error(f"Download error: {e}")
        return jsonify({
            'success': False,
            'error': 'Download error',
            'message': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f"Error in download_video: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal error',
            'message': str(e)
        }), 500

@app.route('/api/stream', methods=['POST'])
@require_api_key
@log_request
def stream_video():
    """Stream video download for large files (experimental)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request', 'message': 'Request body must be JSON'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'error': 'Missing parameter', 'message': 'URL is required'}), 400
        
        format_preference = data.get('format', 'best[ext=mp4]/best')
        
        def generate():
            """Generator function for streaming response"""
            # Create temporary file for streaming
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=True) as tmp_file:
                ydl_opts = {
                    'outtmpl': tmp_file.name,
                    'format': format_preference,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Download to temporary file
                        info = ydl.extract_info(url, download=True)
                        
                        # Stream file contents
                        chunk_size = 4096
                        with open(tmp_file.name, 'rb') as f:
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                yield chunk
                                
                except Exception as e:
                    app.logger.error(f"Streaming error: {e}")
                    yield json.dumps({'error': str(e)}).encode()
        
        return Response(
            stream_with_context(generate()),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': 'attachment; filename="video.mp4"',
                'Cache-Control': 'no-cache',
            }
        )
        
    except Exception as e:
        app.logger.error(f"Error in stream_video: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal error',
            'message': str(e)
        }), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    """Handle file size limit exceeded"""
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {MAX_DOWNLOAD_SIZE_MB}MB'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {e}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@app.before_first_request
def startup_message():
    """Log startup information"""
    app.logger.info("="*80)
    app.logger.info("YT-DLP API SERVER STARTED")
    app.logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    app.logger.info(f"Download directory: {DOWNLOAD_DIR}")
    app.logger.info(f"Max file size: {MAX_DOWNLOAD_SIZE_MB} MB")
    app.logger.info(f"File cleanup after: {MAX_FILE_AGE_MINUTES} minutes")
    app.logger.info(f"API Key configured: {'Yes' if API_KEY != 'change-me-in-production' else 'No (using default)'}")
    app.logger.info("="*80)

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)