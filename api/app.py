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
import base64

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

# Cookie configuration
YOUTUBE_COOKIES_BASE64 = os.environ.get('YOUTUBE_COOKIES_BASE64', '')
USE_COOKIES_FALLBACK = os.environ.get('USE_COOKIES_FALLBACK', 'true').lower() == 'true'
DEFAULT_PLAYER_CLIENT = os.environ.get('DEFAULT_PLAYER_CLIENT', 'tv')
# Default fallback order: TV → iOS → cookies → Android
FALLBACK_ORDER = os.environ.get('FALLBACK_ORDER', 'tv,ios,cookies,android').split(',')

def get_cookies_file():
    """Create temporary cookies file from base64 environment variable"""
    if not YOUTUBE_COOKIES_BASE64:
        return None
    
    try:
        # Decode base64 cookies
        cookies_content = base64.b64decode(YOUTUBE_COOKIES_BASE64).decode('utf-8')
        
        # Create temporary file
        cookies_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        cookies_file.write(cookies_content)
        cookies_file.close()
        
        app.logger.info(f"Created temporary cookies file: {cookies_file.name}")
        return cookies_file.name
    except Exception as e:
        app.logger.error(f"Failed to create cookies file: {e}")
        return None

def cleanup_cookies_file(filepath):
    """Remove temporary cookies file"""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            app.logger.info(f"Cleaned up cookies file: {filepath}")
        except Exception as e:
            app.logger.error(f"Failed to cleanup cookies file: {e}")

def create_ydl_opts_with_fallback(base_opts, url, player_client=None):
    """Create yt-dlp options with fallback strategy"""
    opts = base_opts.copy()
    
    # Use specified player client or default
    if not player_client:
        player_client = DEFAULT_PLAYER_CLIENT
    
    # Apply player client configuration
    if player_client == 'cookies':
        # Use cookies authentication
        cookies_file = get_cookies_file()
        if cookies_file:
            opts['cookiefile'] = cookies_file
            app.logger.info("Using cookie authentication")
            # Schedule cleanup
            threading.Timer(5, lambda: cleanup_cookies_file(cookies_file)).start()
        else:
            app.logger.warning("No cookies available, falling back to ios client")
            opts['extractor_args'] = {'youtube': {'player_client': ['ios']}}
    else:
        # Use player client
        opts['extractor_args'] = {'youtube': {'player_client': [player_client]}}
        app.logger.info(f"Using player client: {player_client}")
    
    return opts

def extract_info_with_fallback(url, base_opts, fallback_order=None, download=False):
    """
    Attempt to extract info (and optionally download) with fallback strategy.
    Returns (success, info, downloaded_file) tuple.
    downloaded_file will be None if download=False.
    """
    if fallback_order is None:
        fallback_order = FALLBACK_ORDER
    
    last_error = None
    cookies_file = None
    
    for method in fallback_order:
        app.logger.info(f"Attempting {'download' if download else 'info extraction'} with method: {method}")
        
        try:
            opts = base_opts.copy()
            
            if method == 'cookies':
                # Use cookies authentication
                if not USE_COOKIES_FALLBACK:
                    app.logger.info("Cookie fallback disabled, skipping")
                    continue
                    
                cookies_file = get_cookies_file()
                if cookies_file:
                    opts['cookiefile'] = cookies_file
                    app.logger.info("Using cookie authentication")
                else:
                    app.logger.warning("No cookies available, skipping cookie method")
                    continue
            else:
                # Use player client
                opts['extractor_args'] = {'youtube': {'player_client': [method]}}
                app.logger.info(f"Using player client: {method}")
            
            # Attempt extraction/download
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=download)
                
                downloaded_file = None
                if download:
                    # Find the downloaded file
                    output_template = opts.get('outtmpl', '')
                    ext = info.get('ext', 'mp4')
                    downloaded_file = output_template.replace('%(ext)s', ext)
                    
                    # Check if file exists
                    if not os.path.exists(downloaded_file):
                        # Try to find file with different extension
                        base_path = os.path.dirname(output_template)
                        base_name = os.path.basename(output_template).split('.')[0]
                        for file in os.listdir(base_path):
                            if file.startswith(base_name):
                                downloaded_file = os.path.join(base_path, file)
                                break
                    
                    if not os.path.exists(downloaded_file):
                        raise Exception(f"Downloaded file not found after {method} download")
                
                app.logger.info(f"✅ {'Download' if download else 'Info extraction'} successful with {method}")
                # Cleanup cookies if used
                if cookies_file:
                    threading.Timer(5, lambda: cleanup_cookies_file(cookies_file)).start()
                return True, info, downloaded_file
                    
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            app.logger.warning(f"❌ {method} failed: {error_msg}")
            
            # Check if it's a format error that might work with another method
            if "Requested format is not available" in error_msg or "HTTP Error 403" in error_msg:
                last_error = e
                continue
            else:
                # This is a more serious error, might affect all methods
                last_error = e
                if "Sign in to confirm" in error_msg:
                    app.logger.info("Bot detection encountered, trying next method")
                    continue
                    
        except Exception as e:
            app.logger.error(f"❌ {method} failed with unexpected error: {e}")
            last_error = e
            continue
    
    # Cleanup cookies if all methods failed
    if cookies_file:
        cleanup_cookies_file(cookies_file)
    
    # All methods failed
    app.logger.error(f"All {'download' if download else 'info extraction'} methods failed. Last error: {last_error}")
    return False, None, None

def download_with_fallback(url, base_opts, fallback_order=None):
    """
    Attempt to download with fallback strategy.
    Returns (success, info, downloaded_file) tuple.
    """
    return extract_info_with_fallback(url, base_opts, fallback_order, download=True)

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
        
        # Get player client preference
        player_client = data.get('player_client', DEFAULT_PLAYER_CLIENT)
        if player_client not in ['ios', 'android', 'mweb', 'web', 'tv', 'cookies']:
            player_client = DEFAULT_PLAYER_CLIENT
        
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'extract_flat': False,
        }
        
        # Use fallback mechanism for info extraction
        if player_client and player_client != 'auto':
            # Create custom fallback order with user-specified client first
            custom_fallback_order = [player_client]
            for method in FALLBACK_ORDER:
                if method != player_client:
                    custom_fallback_order.append(method)
            app.logger.info(f"Using custom fallback order for info: {custom_fallback_order}")
            success, info, _ = extract_info_with_fallback(url, base_opts, custom_fallback_order, download=False)
        else:
            # Use default fallback order
            success, info, _ = extract_info_with_fallback(url, base_opts, download=False)
        
        if not success:
            app.logger.error(f"All info extraction methods failed for URL: {url}")
            return jsonify({
                'success': False,
                'error': 'Info extraction failed',
                'message': 'All methods failed to extract video information. Please try again later.'
            }), 503
        
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
        
        # Get player client preference
        player_client = data.get('player_client', DEFAULT_PLAYER_CLIENT)
        if player_client not in ['ios', 'android', 'mweb', 'web', 'tv', 'cookies']:
            player_client = DEFAULT_PLAYER_CLIENT
        
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
        
        # Base yt-dlp options
        base_opts = {
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
        
        # Always use fallback mechanism, but prioritize user-specified client
        if player_client and player_client != 'auto':
            # Create custom fallback order with user-specified client first
            custom_fallback_order = [player_client]
            # Add remaining methods from default order, excluding the specified one
            for method in FALLBACK_ORDER:
                if method != player_client:
                    custom_fallback_order.append(method)
            app.logger.info(f"Using custom fallback order: {custom_fallback_order}")
            success, info, downloaded_file = download_with_fallback(url, base_opts, custom_fallback_order)
        else:
            # Use default fallback order
            success, info, downloaded_file = download_with_fallback(url, base_opts)
        
        if not success:
            app.logger.error(f"All download methods failed for URL: {url}")
            return jsonify({
                'success': False,
                'error': 'Download failed',
                'message': 'All download methods failed. Please try again later or use a different video.'
            }), 503
        
        # Verify file exists
        if not os.path.exists(downloaded_file):
            app.logger.error(f"Downloaded file not found! Video ID: {video_id}")
            return jsonify({
                'success': False,
                'error': 'Download failed',
                'message': 'File not found after download'
            }), 500
        
        # Log success
        file_size = os.path.getsize(downloaded_file)
        file_size_mb = file_size / (1024 * 1024)
        ext = os.path.splitext(downloaded_file)[1][1:]  # Get extension without dot
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
        
        # Get player client preference
        player_client = data.get('player_client', DEFAULT_PLAYER_CLIENT)
        if player_client not in ['ios', 'android', 'mweb', 'web', 'tv', 'cookies']:
            player_client = DEFAULT_PLAYER_CLIENT
        
        app.logger.info(f"Streaming with player client: {player_client}")
        
        # Pre-validate that we can extract info before starting stream
        test_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
        }
        
        # Determine fallback order
        if player_client and player_client != 'auto':
            custom_fallback_order = [player_client]
            for method in FALLBACK_ORDER:
                if method != player_client:
                    custom_fallback_order.append(method)
            fallback_order = custom_fallback_order
        else:
            fallback_order = FALLBACK_ORDER
        
        # Test which method works
        working_method = None
        for method in fallback_order:
            test_opts_copy = test_opts.copy()
            if method == 'cookies':
                if not USE_COOKIES_FALLBACK:
                    continue
                cookies_file = get_cookies_file()
                if cookies_file:
                    test_opts_copy['cookiefile'] = cookies_file
                    cleanup_cookies_file(cookies_file)
                else:
                    continue
            else:
                test_opts_copy['extractor_args'] = {'youtube': {'player_client': [method]}}
            
            try:
                with yt_dlp.YoutubeDL(test_opts_copy) as ydl:
                    ydl.extract_info(url, download=False)
                    working_method = method
                    app.logger.info(f"Found working method for streaming: {method}")
                    break
            except:
                continue
        
        if not working_method:
            app.logger.error("No working method found for streaming")
            return jsonify({
                'success': False,
                'error': 'Stream failed',
                'message': 'Unable to access video for streaming'
            }), 503
        
        def generate():
            """Generator function for streaming response"""
            # Create temporary file for streaming
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=True) as tmp_file:
                base_opts = {
                    'outtmpl': tmp_file.name,
                    'format': format_preference,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                }
                
                # Use the working method
                if working_method == 'cookies':
                    cookies_file = get_cookies_file()
                    if cookies_file:
                        base_opts['cookiefile'] = cookies_file
                else:
                    base_opts['extractor_args'] = {'youtube': {'player_client': [working_method]}}
                
                try:
                    with yt_dlp.YoutubeDL(base_opts) as ydl:
                        # Download to temporary file
                        info = ydl.extract_info(url, download=True)
                        
                        # Cleanup cookies if used
                        if working_method == 'cookies' and 'cookiefile' in base_opts:
                            cleanup_cookies_file(base_opts['cookiefile'])
                        
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
                    # Cleanup cookies on error
                    if working_method == 'cookies' and 'cookiefile' in base_opts:
                        cleanup_cookies_file(base_opts['cookiefile'])
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

# Call startup message when the module is loaded
startup_message()

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)