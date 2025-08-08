#!/usr/bin/env python3
"""
Test the complete fallback mechanism for the API
"""

import os
import sys
import json
import base64
import tempfile
import yt_dlp

# Test video URLs
TEST_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - usually works
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",   # Me at the zoo - first YouTube video
]

def test_fallback_order():
    """Test the fallback order: iOS → cookies → Android"""
    
    print("="*70)
    print("Testing Fallback Mechanism: iOS → Cookies → Android")
    print("="*70)
    print()
    
    # Define fallback order
    fallback_order = ['ios', 'cookies', 'android']
    
    for url in TEST_URLS:
        print(f"\nTesting URL: {url}")
        print("-"*50)
        
        last_error = None
        success = False
        
        for method in fallback_order:
            print(f"\n→ Trying method: {method}")
            
            # Create options for each method
            ydl_opts = {
                'quiet': True,
                'no_warnings': False,
                'skip_download': True,  # Just test extraction
            }
            
            if method == 'cookies':
                # Check if cookies exist
                if os.path.exists('cookies.txt'):
                    ydl_opts['cookiefile'] = 'cookies.txt'
                    print("  Using cookies.txt")
                else:
                    print("  ❌ No cookies.txt found, skipping")
                    continue
            else:
                # Use player client
                ydl_opts['extractor_args'] = {'youtube': {'player_client': [method]}}
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    print(f"  ✅ SUCCESS with {method}")
                    print(f"  Title: {info.get('title', 'Unknown')}")
                    print(f"  Duration: {info.get('duration_string', 'Unknown')}")
                    
                    # Check available formats
                    formats = info.get('formats', [])
                    video_formats = [f for f in formats if f.get('vcodec') != 'none']
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                    
                    print(f"  Video formats: {len(video_formats)}")
                    print(f"  Audio formats: {len(audio_formats)}")
                    
                    if video_formats:
                        best_video = max(video_formats, 
                                       key=lambda x: x.get('height', 0))
                        print(f"  Best quality: {best_video.get('height', 'Unknown')}p")
                    
                    success = True
                    break
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                print(f"  ❌ FAILED: {error_msg[:100]}...")
                
                # Analyze error
                if "Sign in to confirm" in error_msg:
                    print("  → Bot detection encountered")
                elif "HTTP Error 403" in error_msg:
                    print("  → Access forbidden (403)")
                elif "Requested format is not available" in error_msg:
                    print("  → Format not available")
                
                last_error = e
                continue
                
            except Exception as e:
                print(f"  ❌ UNEXPECTED ERROR: {e}")
                last_error = e
                continue
        
        if not success:
            print(f"\n❌ All methods failed for this URL")
            print(f"Last error: {last_error}")
        else:
            print(f"\n✅ Successfully processed with fallback mechanism")
    
    print("\n" + "="*70)
    print("Fallback Test Complete")
    print("="*70)

def test_specific_method(method):
    """Test a specific download method"""
    
    print(f"\n{'='*70}")
    print(f"Testing Specific Method: {method}")
    print(f"{'='*70}\n")
    
    for url in TEST_URLS:
        print(f"Testing {method} with: {url}")
        
        ydl_opts = {
            'quiet': False,
            'skip_download': True,
        }
        
        if method == 'cookies':
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'
            else:
                print("❌ cookies.txt not found")
                continue
        else:
            ydl_opts['extractor_args'] = {'youtube': {'player_client': [method]}}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"✅ {method} works: {info.get('title')}")
        except Exception as e:
            print(f"❌ {method} failed: {e}")
        
        print()

def main():
    """Main test function"""
    
    print("\n" + "="*70)
    print("YT-DLP API Fallback Mechanism Test")
    print("="*70)
    
    # Test complete fallback chain
    test_fallback_order()
    
    # Optional: Test specific methods
    if len(sys.argv) > 1:
        method = sys.argv[1]
        if method in ['ios', 'android', 'cookies', 'web', 'mweb']:
            test_specific_method(method)
        else:
            print(f"Unknown method: {method}")
            print("Valid methods: ios, android, cookies, web, mweb")

if __name__ == "__main__":
    main()