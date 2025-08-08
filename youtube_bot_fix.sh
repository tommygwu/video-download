#!/bin/bash

# YouTube Bot Detection Bypass Script for yt-dlp
# This script provides multiple methods to bypass YouTube's "Sign in to confirm you're not a bot" error

echo "YouTube Bot Detection Bypass for yt-dlp"
echo "========================================"
echo ""
echo "Select a method to bypass bot detection:"
echo "1. iOS Client (Best quality - includes HD/4K)"
echo "2. Android Client (Basic - 360p only)"
echo "3. Mobile Web Client (Basic - 360p only)"
echo "4. iOS + Chrome cookies (if logged in)"
echo "5. Custom command"
echo ""
read -p "Enter your choice (1-5): " choice

# Get the YouTube URL
read -p "Enter YouTube URL: " url

case $choice in
    1)
        echo "Using iOS client..."
        python3 -m yt_dlp --extractor-args "youtube:player_client=ios" "$url"
        ;;
    2)
        echo "Using Android client..."
        python3 -m yt_dlp --extractor-args "youtube:player_client=android" "$url"
        ;;
    3)
        echo "Using Mobile Web client..."
        python3 -m yt_dlp --extractor-args "youtube:player_client=mweb" "$url"
        ;;
    4)
        echo "Using iOS client with Chrome cookies..."
        python3 -m yt_dlp --extractor-args "youtube:player_client=ios" --cookies-from-browser chrome "$url"
        ;;
    5)
        echo "Enter your custom yt-dlp command (URL will be appended):"
        read -p "Command: python3 -m yt_dlp " custom_args
        python3 -m yt_dlp $custom_args "$url"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac