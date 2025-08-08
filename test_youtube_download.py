#!/usr/bin/env python3
"""
Test YouTube download functionality with fallback mechanisms
Tests both short and long videos with various player clients
"""

import os
import sys
import json
import time
import tempfile
import base64
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yt_dlp

# Test videos
TEST_VIDEOS = {
    'short': {
        'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # "Me at the zoo" - first YouTube video
        'title': 'Me at the zoo',
        'duration': 19,
        'description': 'Short test video - First YouTube video'
    },
    'long': {
        'url': 'https://www.youtube.com/watch?v=EWvNQjAaOHw',  # Longer video as requested
        'title': 'Long test video',
        'duration': None,  # Will be determined during test
        'description': 'Longer video for testing'
    }
}

# Fallback order configurations to test
FALLBACK_CONFIGS = [
    {
        'name': 'Default (TV first)',
        'order': ['tv', 'ios', 'cookies', 'android'],
        'description': 'Default fallback order with TV client first'
    },
    {
        'name': 'iOS first',
        'order': ['ios', 'tv', 'cookies', 'android'],
        'description': 'iOS client prioritized'
    },
    {
        'name': 'Android first',
        'order': ['android', 'tv', 'ios', 'cookies'],
        'description': 'Android client prioritized'
    },
    {
        'name': 'Cookies first',
        'order': ['cookies', 'tv', 'ios', 'android'],
        'description': 'Cookie authentication prioritized'
    }
]

# Age-restricted cookie for testing (base64 encoded)
# This is a sample cookie string - replace with actual YouTube cookies
SAMPLE_COOKIES = """# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+
"""

def create_cookies_file(cookies_content=None):
    """Create a temporary cookies file for testing"""
    if cookies_content is None:
        cookies_content = SAMPLE_COOKIES
    
    cookies_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    cookies_file.write(cookies_content)
    cookies_file.close()
    return cookies_file.name

def test_single_method(url, method, cookies_file=None):
    """Test a single download method"""
    print(f"\n  Testing method: {method}")
    print(f"  {'='*40}")
    
    opts = {
        'quiet': False,
        'no_warnings': False,
        'skip_download': True,  # Only test info extraction
        'noplaylist': True,
    }
    
    if method == 'cookies':
        if cookies_file:
            opts['cookiefile'] = cookies_file
            print(f"  Using cookies file: {cookies_file}")
        else:
            print("  ❌ No cookies file provided, skipping cookies method")
            return False, None, "No cookies file"
    else:
        opts['extractor_args'] = {'youtube': {'player_client': [method]}}
        print(f"  Using player client: {method}")
    
    try:
        start_time = time.time()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            elapsed = time.time() - start_time
            
            print(f"  ✅ SUCCESS in {elapsed:.2f}s")
            print(f"  Title: {info.get('title', 'N/A')}")
            print(f"  Duration: {info.get('duration', 'N/A')}s")
            print(f"  Formats available: {len(info.get('formats', []))}")
            
            # Check if formats are actually available
            if info.get('formats'):
                best_format = max(
                    (f for f in info['formats'] if f.get('height')),
                    key=lambda x: x.get('height', 0),
                    default=None
                )
                if best_format:
                    print(f"  Best quality: {best_format.get('height')}p")
            
            return True, info, None
            
    except yt_dlp.utils.DownloadError as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        
        # Categorize error
        if "Sign in to confirm" in error_msg:
            error_type = "BOT_DETECTION"
            print(f"  ❌ FAILED in {elapsed:.2f}s - Bot detection")
        elif "HTTP Error 400" in error_msg:
            error_type = "HTTP_400"
            print(f"  ❌ FAILED in {elapsed:.2f}s - HTTP 400 Bad Request")
        elif "HTTP Error 403" in error_msg:
            error_type = "HTTP_403"
            print(f"  ❌ FAILED in {elapsed:.2f}s - HTTP 403 Forbidden")
        elif "Unable to download" in error_msg:
            error_type = "DOWNLOAD_ERROR"
            print(f"  ❌ FAILED in {elapsed:.2f}s - Download error")
        else:
            error_type = "OTHER"
            print(f"  ❌ FAILED in {elapsed:.2f}s - {error_msg[:100]}")
        
        return False, None, error_type
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ UNEXPECTED ERROR in {elapsed:.2f}s: {str(e)[:100]}")
        return False, None, "EXCEPTION"

def test_fallback_sequence(url, fallback_order, cookies_file=None):
    """Test a complete fallback sequence"""
    print(f"\nTesting fallback sequence: {fallback_order}")
    print("="*60)
    
    for i, method in enumerate(fallback_order, 1):
        print(f"\nAttempt {i}/{len(fallback_order)}: {method}")
        success, info, error = test_single_method(url, method, cookies_file)
        
        if success:
            print(f"\n🎉 Success with method: {method}")
            return True, method, info
        else:
            if error == "BOT_DETECTION":
                print(f"  → Bot detection, trying next method...")
            elif error == "HTTP_400" and method == "cookies":
                print(f"  → Cookie authentication failed (HTTP 400)")
            elif i < len(fallback_order):
                print(f"  → Failed, trying next method...")
    
    print(f"\n❌ All methods failed for URL: {url}")
    return False, None, None

def run_comprehensive_test():
    """Run comprehensive tests on both videos with different configurations"""
    print("="*80)
    print("YOUTUBE DOWNLOAD TEST SUITE")
    print("="*80)
    
    # Create cookies file for testing
    cookies_file = create_cookies_file()
    print(f"\nCreated test cookies file: {cookies_file}")
    
    results = {
        'short_video': {},
        'long_video': {},
        'summary': {
            'total_tests': 0,
            'successful': 0,
            'failed': 0,
            'methods_working': set(),
            'methods_failing': set()
        }
    }
    
    # Test each video
    for video_key, video_info in TEST_VIDEOS.items():
        print(f"\n{'='*80}")
        print(f"TESTING {video_key.upper()} VIDEO")
        print(f"URL: {video_info['url']}")
        print(f"Expected: {video_info['description']}")
        print("="*80)
        
        video_results = []
        
        # Test individual methods first
        print("\n1. INDIVIDUAL METHOD TESTS")
        print("-"*40)
        
        methods = ['tv', 'ios', 'android', 'cookies']
        for method in methods:
            success, info, error = test_single_method(
                video_info['url'], 
                method, 
                cookies_file if method == 'cookies' else None
            )
            
            video_results.append({
                'method': method,
                'success': success,
                'error': error
            })
            
            results['summary']['total_tests'] += 1
            if success:
                results['summary']['successful'] += 1
                results['summary']['methods_working'].add(method)
            else:
                results['summary']['failed'] += 1
                results['summary']['methods_failing'].add(method)
        
        # Test fallback sequences
        print("\n2. FALLBACK SEQUENCE TESTS")
        print("-"*40)
        
        for config in FALLBACK_CONFIGS:
            print(f"\n{config['name']}: {config['description']}")
            success, working_method, info = test_fallback_sequence(
                video_info['url'],
                config['order'],
                cookies_file
            )
            
            video_results.append({
                'config': config['name'],
                'fallback_order': config['order'],
                'success': success,
                'working_method': working_method
            })
        
        results[f'{video_key}_video'] = video_results
    
    # Cleanup cookies file
    try:
        os.remove(cookies_file)
        print(f"\nCleaned up cookies file: {cookies_file}")
    except:
        pass
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\nTotal tests run: {results['summary']['total_tests']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    
    if results['summary']['methods_working']:
        print(f"\n✅ Working methods: {', '.join(results['summary']['methods_working'])}")
    
    if results['summary']['methods_failing']:
        print(f"❌ Failing methods: {', '.join(results['summary']['methods_failing'])}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if 'tv' in results['summary']['methods_working']:
        print("✓ TV client is working - recommended as primary method")
    elif 'ios' in results['summary']['methods_working']:
        print("✓ iOS client is working - recommended as primary method")
    elif 'android' in results['summary']['methods_working']:
        print("✓ Android client is working - recommended as primary method")
    else:
        print("⚠️  No player clients working reliably - cookies authentication may be required")
    
    if 'cookies' in results['summary']['methods_failing']:
        print("⚠️  Cookie authentication is failing - check cookie format and validity")
    
    return results

def test_actual_download(url, method='tv'):
    """Test actual video download (not just info extraction)"""
    print(f"\nTesting actual download with {method} client...")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'test_video.%(ext)s')
        
        opts = {
            'outtmpl': output_file,
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'extractor_args': {'youtube': {'player_client': [method]}}
        }
        
        try:
            start_time = time.time()
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                elapsed = time.time() - start_time
                
                # Find downloaded file
                downloaded_files = list(Path(tmpdir).glob('test_video.*'))
                if downloaded_files:
                    file_path = downloaded_files[0]
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    
                    print(f"✅ Download successful in {elapsed:.2f}s")
                    print(f"   File: {file_path.name}")
                    print(f"   Size: {file_size:.2f} MB")
                    print(f"   Title: {info.get('title', 'N/A')}")
                    return True
                else:
                    print(f"❌ Download completed but file not found")
                    return False
                    
        except Exception as e:
            print(f"❌ Download failed: {str(e)[:200]}")
            return False

if __name__ == '__main__':
    # Run comprehensive tests
    results = run_comprehensive_test()
    
    # Optionally test actual download with a working method
    if results['summary']['methods_working']:
        working_method = list(results['summary']['methods_working'])[0]
        print(f"\n{'='*80}")
        print("ACTUAL DOWNLOAD TEST")
        print("="*80)
        test_actual_download(TEST_VIDEOS['short']['url'], working_method)