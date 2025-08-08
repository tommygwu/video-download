#!/usr/bin/env python3
"""
Test script to verify cookie fallback mechanism
"""

import os
import sys
import base64
import tempfile
import yt_dlp

# Test YouTube URL
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def test_ios_client():
    """Test iOS client"""
    print("Testing iOS client...")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            print(f"✅ iOS client working: {info.get('title')}")
            return True
    except Exception as e:
        print(f"❌ iOS client failed: {e}")
        return False

def test_cookie_auth():
    """Test cookie authentication"""
    print("\nTesting cookie authentication...")
    
    # Check if cookies.txt exists
    if not os.path.exists('cookies.txt'):
        print("❌ cookies.txt not found. Run export_youtube_cookies.py first")
        return False
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            print(f"✅ Cookie auth working: {info.get('title')}")
            return True
    except Exception as e:
        print(f"❌ Cookie auth failed: {e}")
        return False

def test_base64_cookies():
    """Test base64 cookie encoding/decoding"""
    print("\nTesting base64 cookie encoding...")
    
    if not os.path.exists('cookies.txt'):
        print("❌ cookies.txt not found")
        return False
    
    try:
        # Read cookies
        with open('cookies.txt', 'r') as f:
            cookies_content = f.read()
        
        # Encode to base64
        cookies_base64 = base64.b64encode(cookies_content.encode()).decode()
        print(f"✅ Encoded cookies to base64 ({len(cookies_base64)} chars)")
        
        # Decode back
        decoded = base64.b64decode(cookies_base64).decode()
        
        # Verify
        if decoded == cookies_content:
            print("✅ Base64 encoding/decoding verified")
            
            # Test with decoded cookies
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write(decoded)
                tmp_path = tmp.name
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'cookiefile': tmp_path
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(TEST_URL, download=False)
                    print(f"✅ Decoded cookies working: {info.get('title')}")
                    os.unlink(tmp_path)
                    return True
            except Exception as e:
                print(f"❌ Decoded cookies failed: {e}")
                os.unlink(tmp_path)
                return False
        else:
            print("❌ Base64 decode mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Base64 test failed: {e}")
        return False

def test_android_client():
    """Test Android client"""
    print("\nTesting Android client...")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            print(f"✅ Android client working: {info.get('title')}")
            return True
    except Exception as e:
        print(f"❌ Android client failed: {e}")
        return False

def main():
    print("="*60)
    print("Cookie Fallback Mechanism Test")
    print("="*60)
    print(f"Test URL: {TEST_URL}")
    print()
    
    results = {
        'iOS': test_ios_client(),
        'Cookies': test_cookie_auth(),
        'Base64': test_base64_cookies(),
        'Android': test_android_client()
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for method, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{method:10} : {status}")
    
    print("\n" + "="*60)
    print("Recommended Fallback Order:")
    print("="*60)
    
    working_methods = [m for m, s in results.items() if s]
    if working_methods:
        print(f"1. {', '.join(working_methods)}")
        print("\nSet in Render.com:")
        if 'Cookies' in working_methods:
            print("FALLBACK_ORDER=ios,cookies,android")
        else:
            print("FALLBACK_ORDER=ios,android")
    else:
        print("❌ No methods working! Check your setup.")
    
    print()

if __name__ == "__main__":
    main()