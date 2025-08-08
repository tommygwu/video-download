#!/usr/bin/env python3
"""Quick test to verify YouTube download works with fallback"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yt_dlp
import tempfile

def test_download(url, player_client):
    """Test download with specific player client"""
    print(f"\nTesting {player_client} client with URL: {url}")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, 'test.%(ext)s')
        
        opts = {
            'outtmpl': output,
            'format': 'best[height<=480]/best',  # Lower quality for faster test
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'extractor_args': {'youtube': {'player_client': [player_client]}}
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                print(f"✅ SUCCESS - Downloaded: {info.get('title')}")
                
                # Check file
                files = os.listdir(tmpdir)
                if files:
                    file_size = os.path.getsize(os.path.join(tmpdir, files[0])) / (1024*1024)
                    print(f"   File: {files[0]} ({file_size:.2f} MB)")
                return True
        except Exception as e:
            print(f"❌ FAILED: {str(e)[:100]}")
            return False

# Test URLs
urls = [
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo
    "https://www.youtube.com/watch?v=EWvNQjAaOHw",  # How I use LLMs
]

# Test different clients
clients = ['ios', 'android', 'web']

print("QUICK YOUTUBE DOWNLOAD TEST")
print("="*60)

success_count = 0
fail_count = 0

for url in urls:
    for client in clients:
        if test_download(url, client):
            success_count += 1
            break  # One success is enough per URL
        else:
            fail_count += 1

print("\n" + "="*60)
print(f"SUMMARY: {success_count} successful downloads")
print("="*60)