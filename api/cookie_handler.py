"""
Cookie handler for YouTube authentication
Handles cookie parsing, validation and creation
"""

import base64
import tempfile
import os
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

def parse_netscape_cookies(cookie_content: str) -> List[Dict]:
    """Parse Netscape format cookies into a list of cookie dictionaries"""
    cookies = []
    lines = cookie_content.strip().split('\n')
    
    for line in lines:
        # Skip comments and empty lines
        if line.startswith('#') or not line.strip():
            continue
        
        # Parse cookie fields (Netscape format has 7 fields)
        parts = line.split('\t')
        if len(parts) >= 7:
            cookie = {
                'domain': parts[0],
                'include_subdomains': parts[1] == 'TRUE',
                'path': parts[2],
                'secure': parts[3] == 'TRUE',
                'expires': int(parts[4]) if parts[4] != '0' else None,
                'name': parts[5],
                'value': parts[6] if len(parts) > 6 else ''
            }
            cookies.append(cookie)
    
    return cookies

def create_youtube_cookies_file(cookies_base64: Optional[str] = None) -> Optional[str]:
    """
    Create a temporary cookies file for YouTube authentication
    
    Args:
        cookies_base64: Base64 encoded cookies in Netscape format
        
    Returns:
        Path to temporary cookies file or None if creation failed
    """
    if not cookies_base64:
        logger.warning("No cookies provided")
        return None
    
    try:
        # Decode base64 cookies
        cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
        
        # Validate cookie format
        if not cookies_content.strip():
            logger.error("Empty cookies content")
            return None
        
        # Parse cookies to validate format
        parsed_cookies = parse_netscape_cookies(cookies_content)
        
        # Check for essential YouTube cookies
        cookie_names = {c['name'] for c in parsed_cookies}
        essential_cookies = ['CONSENT', 'SID', 'HSID', 'SSID', 'APISID', 'SAPISID']
        
        # At least some essential cookies should be present
        found_essential = [name for name in essential_cookies if name in cookie_names]
        if not found_essential and not any('LOGIN' in name for name in cookie_names):
            logger.warning(f"Missing essential YouTube cookies. Found: {cookie_names}")
        
        # Create temporary file
        cookies_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.txt', 
            delete=False,
            prefix='yt_cookies_'
        )
        
        # Write Netscape header if not present
        if not cookies_content.startswith('# Netscape HTTP Cookie File'):
            cookies_file.write('# Netscape HTTP Cookie File\n')
            cookies_file.write('# This is a generated file! Do not edit.\n')
        
        cookies_file.write(cookies_content)
        if not cookies_content.endswith('\n'):
            cookies_file.write('\n')
        
        cookies_file.close()
        
        logger.info(f"Created cookies file: {cookies_file.name}")
        logger.debug(f"Cookies file contains {len(parsed_cookies)} cookies")
        
        return cookies_file.name
        
    except base64.binascii.Error as e:
        logger.error(f"Failed to decode base64 cookies: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode cookies as UTF-8: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating cookies file: {e}")
        return None

def validate_cookies_for_youtube(cookies_file: str) -> bool:
    """
    Validate that cookies file has necessary YouTube cookies
    
    Args:
        cookies_file: Path to cookies file
        
    Returns:
        True if cookies appear valid for YouTube
    """
    try:
        with open(cookies_file, 'r') as f:
            content = f.read()
        
        cookies = parse_netscape_cookies(content)
        
        # Check for YouTube domains
        youtube_domains = ['.youtube.com', 'youtube.com', '.google.com']
        youtube_cookies = [c for c in cookies if any(d in c['domain'] for d in youtube_domains)]
        
        if not youtube_cookies:
            logger.warning("No YouTube domain cookies found")
            return False
        
        # Check for authentication cookies
        auth_cookie_names = ['SID', 'HSID', 'SSID', 'APISID', 'SAPISID', 'LOGIN_INFO']
        auth_cookies = [c for c in youtube_cookies if c['name'] in auth_cookie_names]
        
        if auth_cookies:
            logger.info(f"Found {len(auth_cookies)} authentication cookies")
            return True
        
        # Check for CONSENT cookie (minimum for age-restricted videos)
        consent_cookies = [c for c in youtube_cookies if c['name'] == 'CONSENT']
        if consent_cookies:
            logger.info("Found CONSENT cookie for age-restricted content")
            return True
        
        logger.warning("No authentication or consent cookies found")
        return False
        
    except Exception as e:
        logger.error(f"Error validating cookies: {e}")
        return False

def cleanup_cookies_file(filepath: str) -> None:
    """
    Safely remove temporary cookies file
    
    Args:
        filepath: Path to cookies file to remove
    """
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.debug(f"Removed cookies file: {filepath}")
        except Exception as e:
            logger.error(f"Failed to remove cookies file {filepath}: {e}")

# Sample cookies for age-restricted content (CONSENT cookie)
SAMPLE_AGE_RESTRICTED_COOKIES = """# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	2147483647	CONSENT	YES+cb.20210328-17-p0.en+FX+999
.youtube.com	TRUE	/	FALSE	0	VISITOR_INFO1_LIVE	a0b1c2d3e4f5
"""

def get_sample_cookies() -> str:
    """Get sample cookies for testing (base64 encoded)"""
    return base64.b64encode(SAMPLE_AGE_RESTRICTED_COOKIES.encode()).decode()