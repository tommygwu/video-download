#!/bin/bash

# Clean Download Script for YouTube videos
# Uses the clean logger to provide condensed, meaningful output

# Colors for output (optional)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Clean YouTube Downloader - Condensed Logging"
    echo "============================================"
    echo ""
    echo "Usage: $0 [OPTIONS] <YouTube URL>"
    echo ""
    echo "Options:"
    echo "  -c, --client CLIENT    Use specific client (ios/android/mweb) [default: ios]"
    echo "  -f, --format FORMAT    Specify video format to download"
    echo "  -o, --output NAME      Output filename template"
    echo "  -l, --log FILE         Save logs to file"
    echo "  -v, --verbose          Show more detailed logging"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 \"https://youtube.com/watch?v=dQw4w9WgXcQ\""
    echo "  $0 -c android \"https://youtube.com/watch?v=dQw4w9WgXcQ\""
    echo "  $0 -f best -l download.log \"https://youtube.com/watch?v=dQw4w9WgXcQ\""
    exit 0
}

# Parse command line arguments
CLIENT="ios"
FORMAT=""
OUTPUT=""
LOG_FILE=""
VERBOSE=""
URL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--client)
            CLIENT="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="--format $2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="--output $2"
            shift 2
            ;;
        -l|--log)
            LOG_FILE="--log-file $2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            URL="$1"
            shift
            ;;
    esac
done

# Check if URL is provided
if [ -z "$URL" ]; then
    echo -e "${RED}Error: No YouTube URL provided${NC}"
    echo ""
    usage
fi

# Validate client
if [[ ! "$CLIENT" =~ ^(ios|android|mweb|web)$ ]]; then
    echo -e "${RED}Error: Invalid client '$CLIENT'${NC}"
    echo "Valid clients: ios, android, mweb, web"
    exit 1
fi

# Display starting message
echo -e "${BLUE}Clean YouTube Downloader${NC}"
echo "========================"
echo -e "Client: ${GREEN}$CLIENT${NC}"
echo -e "URL: ${YELLOW}$URL${NC}"
echo ""

# Run the clean logger
python3 /Users/twu/GitHub/video-download/yt_dlp_clean_logger.py \
    --client "$CLIENT" \
    $FORMAT \
    $OUTPUT \
    $LOG_FILE \
    $VERBOSE \
    "$URL"

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Download completed successfully${NC}"
else
    echo -e "\n${RED}❌ Download failed${NC}"
    exit 1
fi