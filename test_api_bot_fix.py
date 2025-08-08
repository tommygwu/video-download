#!/usr/bin/env python3
"""
Test script to verify YouTube bot detection bypass in the API
"""

import requests
import json
import sys

# Configuration
API_URL = "http://localhost:5000"
API_KEY = "change-me-in-production"  # Default API key from app.py
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

def test_info_endpoint():
    """Test the /api/info endpoint with iOS player client"""
    print("Testing /api/info endpoint...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test with default (iOS) client
    data = {
        "url": TEST_VIDEO_URL
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/info",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            info = response.json()
            if info.get('success'):
                print(f"✅ Info endpoint working with iOS client (default)")
                print(f"   Title: {info['data']['title']}")
                print(f"   Duration: {info['data']['duration_string']}")
                print(f"   Uploader: {info['data']['uploader']}")
            else:
                print(f"❌ Info endpoint failed: {info.get('message')}")
                return False
        else:
            print(f"❌ Info endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Error testing info endpoint: {e}")
        return False
    
    # Test with explicit Android client
    print("\nTesting with Android client...")
    data['player_client'] = 'android'
    
    try:
        response = requests.post(
            f"{API_URL}/api/info",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            print("✅ Info endpoint working with Android client")
        else:
            print(f"⚠️  Android client returned status {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Error with Android client: {e}")
    
    return True

def main():
    print("="*60)
    print("YouTube Bot Detection Bypass API Test")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Test Video: {TEST_VIDEO_URL}")
    print("="*60)
    print()
    
    # Make sure the API server is running
    print("Checking API server health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API server is healthy")
            print(f"   Version: {health.get('version')}")
            print(f"   Free disk: {health.get('free_disk_mb')} MB")
        else:
            print(f"⚠️  Health check returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running!")
        print("   Start it with: python3 api/app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        sys.exit(1)
    
    print()
    
    # Test the info endpoint
    if test_info_endpoint():
        print("\n" + "="*60)
        print("✅ API is successfully bypassing YouTube bot detection!")
        print("="*60)
        print("\nThe API now supports the following parameters:")
        print("  - player_client: 'ios' (default), 'android', 'mweb', 'web'")
        print("\nExample API request:")
        print(json.dumps({
            "url": "https://youtube.com/watch?v=VIDEO_ID",
            "player_client": "ios"  # Optional, defaults to iOS
        }, indent=2))
    else:
        print("\n❌ Bot detection bypass test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()