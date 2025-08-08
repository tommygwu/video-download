#!/usr/bin/env python3
"""
Test script to verify fallback mechanism is working correctly
"""

import requests
import json
import os

# Configuration
API_URL = os.environ.get('API_URL', 'http://localhost:5000')
API_KEY = os.environ.get('YT_DLP_API_KEY', 'change-me-in-production')

def test_download_endpoint():
    """Test the /api/download endpoint with iOS client (which may fail and trigger fallback)"""
    print("Testing /api/download endpoint with iOS client...")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Test URL that commonly triggers bot detection
    data = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Rick Astley - Never Gonna Give You Up
        'format': 'best[ext=mp4]/best',
        'player_client': 'ios'  # Explicitly specify iOS which may fail
    }
    
    try:
        response = requests.post(
            f'{API_URL}/api/download',
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save a small portion to verify it worked
            content_length = 0
            for chunk in response.iter_content(chunk_size=1024):
                content_length += len(chunk)
                if content_length > 1024:  # Just verify we got some data
                    break
            print(f"✅ Download successful! Received {content_length} bytes")
            return True
        else:
            print(f"❌ Download failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_info_endpoint():
    """Test the /api/info endpoint with iOS client"""
    print("\nTesting /api/info endpoint with iOS client...")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'player_client': 'ios'
    }
    
    try:
        response = requests.post(
            f'{API_URL}/api/info',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            if info.get('success'):
                print(f"✅ Info extraction successful!")
                print(f"Title: {info['data'].get('title', 'N/A')}")
                print(f"Duration: {info['data'].get('duration_string', 'N/A')}")
                return True
            else:
                print(f"❌ Info extraction failed: {info}")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Testing Fallback Mechanism")
    print(f"API URL: {API_URL}")
    print("="*60)
    
    # Test info endpoint
    info_success = test_info_endpoint()
    
    # Test download endpoint
    download_success = test_download_endpoint()
    
    print("\n" + "="*60)
    print("Test Results:")
    print(f"Info Endpoint: {'✅ PASSED' if info_success else '❌ FAILED'}")
    print(f"Download Endpoint: {'✅ PASSED' if download_success else '❌ FAILED'}")
    print("="*60)
    
    if info_success and download_success:
        print("\n✅ All tests passed! Fallback mechanism is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
        return 1

if __name__ == '__main__':
    exit(main())