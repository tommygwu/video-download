# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

yt-dlp is a feature-rich command-line audio/video downloader with support for thousands of sites. It's a fork of youtube-dl that extracts and downloads media from various platforms.

## Key Commands

### Development & Testing
```bash
# Run yt-dlp directly
python3 -m yt_dlp [options] [URL]

# Run tests (all)
make test
# Or with pytest directly
python -m pytest -Werror

# Run offline tests only (no download tests)
make offlinetest
# Or
python -m pytest -Werror -m "not download"

# Run specific test
python devscripts/run_tests.py test_NAME
# Or
python -m pytest test/test_NAME.py

# Run a single test method
python -m pytest test/test_download.py::TestDownload::test_Youtube
```

### Code Quality
```bash
# Run linting and formatting checks
make codetest

# Run ruff linter
ruff check .

# Check code formatting
autopep8 --diff .

# Fix code formatting
autopep8 --in-place .
```

### Build & Installation
```bash
# Build the standalone executable
make

# Generate lazy extractors (required before running)
make lazy-extractors

# Install locally
make install

# Clean build artifacts
make clean
make clean-all
```

## Architecture Overview

### Core Components

1. **YoutubeDL** (`yt_dlp/YoutubeDL.py`)
   - Central orchestrator class that coordinates the entire download process
   - Handles configuration, extractor selection, downloading, and post-processing
   - Manages the workflow: URL parsing → extraction → download → post-processing

2. **Extractors** (`yt_dlp/extractor/`)
   - Each site has its own extractor class inheriting from `InfoExtractor`
   - `common.py` contains the base `InfoExtractor` class with shared functionality
   - `_extractors.py` lists all available extractors
   - Extractors parse site-specific formats and return standardized info dictionaries

3. **Downloaders** (`yt_dlp/downloader/`)
   - Protocol-specific downloaders (HTTP, HLS, DASH, F4M, etc.)
   - `common.py` contains base `FileDownloader` class
   - Fragment-based downloaders for streaming protocols
   - External downloader support (aria2c, wget, curl, etc.)

4. **Post-processors** (`yt_dlp/postprocessor/`)
   - FFmpeg-based processors for format conversion, merging, metadata
   - Thumbnail embedding, subtitle conversion
   - SponsorBlock integration
   - Metadata manipulation

5. **Networking** (`yt_dlp/networking/`)
   - Request handling, impersonation, WebSocket support
   - Cookie management, proxy support
   - Custom protocol handlers

### Key Design Patterns

- **Info Dictionary**: Extractors return standardized dictionaries containing video metadata, formats, subtitles, etc. This is the primary data structure passed between components.

- **Options Dictionary**: Configuration passed from CLI/API through YoutubeDL to all components

- **Format Selection**: Sophisticated format filtering and sorting system allowing users to specify quality, codec, and other preferences

- **Plugin System**: Supports external extractors and post-processors via `yt_dlp_plugins` namespace

### Testing Approach

- **Offline tests**: Most tests mock network responses for reliability
- **Download tests**: Real download tests marked with `@pytest.mark.download`
- **Extractor tests**: Each extractor can have test cases defined with example URLs
- Test data stored in `test/testdata/` for consistency

## Important Implementation Notes

- Python 3.9+ required
- Uses lazy loading for extractors to improve startup time
- Extensive use of regex for HTML/JSON parsing
- FFmpeg is optional but required for many post-processing features
- Cookie support for authenticated extraction
- Comprehensive format selection language for filtering downloads

## Common Development Tasks

### Adding a new extractor
1. Create new file in `yt_dlp/extractor/` inheriting from `InfoExtractor`
2. Add to `_extractors.py`
3. Implement `_real_extract()` method
4. Add test cases with `_TESTS` class variable

### Debugging an extractor
```bash
# Verbose output
python3 -m yt_dlp -v [URL]

# Print traffic
python3 -m yt_dlp --print-traffic [URL]

# Dump full info dictionary
python3 -m yt_dlp --dump-json [URL]
```

### Testing format selection
```bash
# List available formats
python3 -m yt_dlp -F [URL]

# Simulate download
python3 -m yt_dlp -s [URL]
```