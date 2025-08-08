#!/usr/bin/env python3
"""
Clean Logger for yt-dlp
Provides condensed, meaningful logging for YouTube downloads while filtering noise
"""

import subprocess
import sys
import re
import time
import argparse
from datetime import datetime, timedelta
from threading import Thread, Lock
import queue
import json

class CleanLogger:
    def __init__(self, log_file=None, verbose=False):
        self.log_file = log_file
        self.verbose = verbose
        self.health_check_count = 0
        self.last_health_report = datetime.now()
        self.download_complete = False
        self.video_title = None
        self.video_url = None
        self.last_progress = 0
        self.server_alive = True
        self.start_time = datetime.now()
        self.log_queue = queue.Queue()
        self.lock = Lock()
        
        # Regex patterns
        self.health_pattern = re.compile(r'GET /health')
        self.url_pattern = re.compile(r'\[youtube\] ([^\s:]+):\s+Downloading')
        self.title_pattern = re.compile(r'\[download\] Destination: (.+)')
        self.progress_pattern = re.compile(r'\[download\]\s+(\d+\.?\d*)%')
        self.complete_pattern = re.compile(r'\[download\] 100%|has already been downloaded')
        self.error_pattern = re.compile(r'ERROR:|WARNING:')
        self.api_pattern = re.compile(r'Downloading (android|ios|mweb|web) (?:player )?API')
        
    def timestamp(self):
        """Return formatted timestamp"""
        return datetime.now().strftime("[%H:%M:%S]")
    
    def log(self, message, force=False):
        """Output log message"""
        if self.download_complete and not force:
            return
            
        print(message)
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
    
    def process_line(self, line):
        """Process a single line of output"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return
            
        # Track health checks silently
        if self.health_pattern.search(line):
            with self.lock:
                self.health_check_count += 1
            return
            
        # Check for 5-minute health report interval
        now = datetime.now()
        if (now - self.last_health_report) >= timedelta(minutes=5) and self.health_check_count > 0:
            self.log(f"{self.timestamp()} 💚 Server alive - Health checks: {self.health_check_count} total")
            self.last_health_report = now
            
        # Capture video URL
        url_match = self.url_pattern.search(line)
        if url_match:
            self.video_url = url_match.group(1)
            
        # Capture API client being used
        api_match = self.api_pattern.search(line)
        if api_match:
            client = api_match.group(1)
            self.log(f"{self.timestamp()} 🔧 Using {client.upper()} client to bypass bot detection")
            return
            
        # Capture video title
        title_match = self.title_pattern.search(line)
        if title_match:
            self.video_title = title_match.group(1).split('/')[-1]  # Get filename only
            self.log(f"{self.timestamp()} 🎬 Downloading: \"{self.video_title}\"")
            return
            
        # Track download progress at milestones
        progress_match = self.progress_pattern.search(line)
        if progress_match:
            progress = float(progress_match.group(1))
            # Report at 25%, 50%, 75% milestones
            if progress >= 25 and self.last_progress < 25:
                self.log(f"{self.timestamp()} 📊 Download progress: 25% complete")
                self.last_progress = 25
            elif progress >= 50 and self.last_progress < 50:
                self.log(f"{self.timestamp()} 📊 Download progress: 50% complete")
                self.last_progress = 50
            elif progress >= 75 and self.last_progress < 75:
                self.log(f"{self.timestamp()} 📊 Download progress: 75% complete")
                self.last_progress = 75
            return
            
        # Check for completion
        if self.complete_pattern.search(line):
            if not self.download_complete:
                title_display = self.video_title or self.video_url or "video"
                self.log(f"{self.timestamp()} ✅ Download complete: \"{title_display}\"")
                self.log(f"{self.timestamp()} 🔇 Logging paused until shutdown")
                self.download_complete = True
            return
            
        # Always show errors and warnings
        if self.error_pattern.search(line):
            self.log(f"{self.timestamp()} ⚠️ {line}", force=True)
            return
            
        # In verbose mode, show other important lines
        if self.verbose and any(keyword in line.lower() for keyword in 
                                ['downloading', 'extracting', 'format', 'merged']):
            self.log(f"{self.timestamp()} 📝 {line}")
            
    def health_check_reporter(self):
        """Background thread to report health checks every 5 minutes"""
        while not self.download_complete:
            time.sleep(300)  # 5 minutes
            if self.health_check_count > 0 and not self.download_complete:
                with self.lock:
                    self.log(f"{self.timestamp()} 💚 Server alive - Health checks: {self.health_check_count} total")
                    
    def run_yt_dlp(self, url, client='ios', extra_args=None):
        """Run yt-dlp with clean logging"""
        # Start with initial message
        self.log(f"{self.timestamp()} 🎬 Starting download: {url}")
        
        # Build command
        cmd = [
            'python3', '-m', 'yt_dlp',
            '--extractor-args', f'youtube:player_client={client}',
        ]
        
        if extra_args:
            cmd.extend(extra_args)
            
        cmd.append(url)
        
        # Start health check reporter thread
        health_thread = Thread(target=self.health_check_reporter, daemon=True)
        health_thread.start()
        
        # Report initial health checks after 5 seconds
        initial_health_timer = Thread(
            target=lambda: (
                time.sleep(5),
                self.log(f"{self.timestamp()} ✅ Health checks active ({self.health_check_count} received)")
                if self.health_check_count > 0 else None
            ),
            daemon=True
        )
        initial_health_timer.start()
        
        try:
            # Run yt-dlp and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Process output line by line
            for line in process.stdout:
                self.process_line(line)
                
            process.wait()
            
            # If process ended without download complete message
            if not self.download_complete and process.returncode == 0:
                self.log(f"{self.timestamp()} ✅ Process completed")
                self.download_complete = True
                
            return process.returncode
            
        except KeyboardInterrupt:
            self.log(f"{self.timestamp()} ⏹️ Download interrupted by user", force=True)
            process.terminate()
            return 1
        except Exception as e:
            self.log(f"{self.timestamp()} ❌ Error: {str(e)}", force=True)
            return 1

def main():
    parser = argparse.ArgumentParser(
        description='Clean logging wrapper for yt-dlp YouTube downloads',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://youtube.com/watch?v=..."
  %(prog)s --client android "https://youtube.com/watch?v=..."
  %(prog)s --log-file download.log "https://youtube.com/watch?v=..."
  %(prog)s -v "https://youtube.com/watch?v=..."  # Verbose mode
        """
    )
    
    parser.add_argument('url', help='YouTube URL to download')
    parser.add_argument('--client', '-c', 
                       choices=['ios', 'android', 'mweb', 'web'],
                       default='ios',
                       help='YouTube client to use (default: ios)')
    parser.add_argument('--log-file', '-l',
                       help='Save logs to file')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Show more detailed logging')
    parser.add_argument('--format', '-f',
                       help='Video format to download')
    parser.add_argument('--output', '-o',
                       help='Output filename template')
    
    args = parser.parse_args()
    
    # Build extra arguments for yt-dlp
    extra_args = []
    if args.format:
        extra_args.extend(['-f', args.format])
    if args.output:
        extra_args.extend(['-o', args.output])
    
    # Create logger and run
    logger = CleanLogger(log_file=args.log_file, verbose=args.verbose)
    
    try:
        exit_code = logger.run_yt_dlp(args.url, args.client, extra_args)
        
        # Simulate waiting for shutdown (in real scenario, this would be handled differently)
        if exit_code == 0 and logger.download_complete:
            print("\n[Press Ctrl+C to simulate instance shutdown]")
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.log(f"{logger.timestamp()} ⏹️ Instance shutting down due to inactivity", force=True)
                
    except KeyboardInterrupt:
        logger.log(f"{logger.timestamp()} ⏹️ Process terminated by user", force=True)
        sys.exit(1)
        
    sys.exit(exit_code)

if __name__ == '__main__':
    main()