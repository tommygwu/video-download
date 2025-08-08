#!/usr/bin/env python3
"""
Test to compare format availability between iOS and Android clients
"""

import yt_dlp
import sys

# Test URL
test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

print("Comparing format availability between iOS and Android clients")
print("="*60)

# Test with iOS client
print('\nTesting iOS client:')
print("-"*40)
ios_opts = {
    'quiet': True,
    'skip_download': True,
    'extractor_args': {'youtube': {'player_client': ['ios']}},
}

try:
    with yt_dlp.YoutubeDL(ios_opts) as ydl:
        info = ydl.extract_info(test_url, download=False)
        formats = info.get('formats', [])
        print(f'Total formats available: {len(formats)}')
        
        # Get MP4 formats with resolution
        mp4_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('height')]
        if mp4_formats:
            mp4_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            print(f'MP4 formats with resolution: {len(mp4_formats)}')
            print('\nTop 5 MP4 formats:')
            for f in mp4_formats[:5]:
                filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                size_mb = filesize / (1024*1024) if filesize else 0
                print(f"  {f.get('format_id'):>4}: {f.get('height'):>4}p - {f.get('vcodec', 'N/A'):>8} - {size_mb:>6.1f} MB - {f.get('format_note', '')}")
            
            highest = mp4_formats[0]
            print(f'\nHighest MP4 resolution: {highest.get("height")}p (format {highest.get("format_id")})')
        
        # Show all formats with audio and video
        combined_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') != 'none' and f.get('height')]
        if combined_formats:
            combined_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            print(f'\nFormats with both audio+video: {len(combined_formats)}')
            print('Top 3 combined formats:')
            for f in combined_formats[:3]:
                print(f"  {f.get('format_id'):>4}: {f.get('height'):>4}p - {f.get('ext'):>4} - {f.get('format_note', '')}")
            
except Exception as e:
    print(f'iOS failed: {e}')

print('\n' + '='*60)

# Test with Android client
print('\nTesting Android client:')
print("-"*40)
android_opts = {
    'quiet': True,
    'skip_download': True,
    'extractor_args': {'youtube': {'player_client': ['android']}},
}

try:
    with yt_dlp.YoutubeDL(android_opts) as ydl:
        info = ydl.extract_info(test_url, download=False)
        formats = info.get('formats', [])
        print(f'Total formats available: {len(formats)}')
        
        # Get MP4 formats with resolution
        mp4_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('height')]
        if mp4_formats:
            mp4_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            print(f'MP4 formats with resolution: {len(mp4_formats)}')
            print('\nTop 5 MP4 formats:')
            for f in mp4_formats[:5]:
                filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                size_mb = filesize / (1024*1024) if filesize else 0
                print(f"  {f.get('format_id'):>4}: {f.get('height'):>4}p - {f.get('vcodec', 'N/A'):>8} - {size_mb:>6.1f} MB - {f.get('format_note', '')}")
            
            highest = mp4_formats[0]
            print(f'\nHighest MP4 resolution: {highest.get("height")}p (format {highest.get("format_id")})')
        
        # Show all formats with audio and video
        combined_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') != 'none' and f.get('height')]
        if combined_formats:
            combined_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            print(f'\nFormats with both audio+video: {len(combined_formats)}')
            print('Top 3 combined formats:')
            for f in combined_formats[:3]:
                print(f"  {f.get('format_id'):>4}: {f.get('height'):>4}p - {f.get('ext'):>4} - {f.get('format_note', '')}")
        
        # Check for 3gp format (17)
        format_17 = next((f for f in formats if f.get('format_id') == '17'), None)
        if format_17:
            print(f"\nFormat 17 (3gp) available: {format_17.get('height', 'N/A')}p")
            
except Exception as e:
    print(f'Android failed: {e}')

print('\n' + '='*60)
print('Summary:')
print('iOS typically provides higher quality formats and better codec support.')
print('Android may have more restricted format availability.')
print('The actual formats depend on the video and YouTube\'s current policies.')