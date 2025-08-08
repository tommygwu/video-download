#!/usr/bin/env python3
"""
Export YouTube cookies from Chrome on macOS - SECURITY-FOCUSED VERSION
Outputs a base64-encoded cookie string for use with Render.com deployment

SECURITY WARNING: YouTube cookies can provide access to your Google account!
Consider using a dedicated YouTube account for downloads.
"""

import os
import sys
import sqlite3
import tempfile
import base64
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Try to import Chrome cookie decryption dependencies
try:
    import keyring
    import Crypto.Cipher.AES
    import Crypto.Protocol.KDF
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: pycryptodome not installed. Cookies may not be decrypted.")
    print("Install with: pip3 install pycryptodome keyring")

# Define cookie categories
ESSENTIAL_COOKIES = [
    'VISITOR_INFO1_LIVE',  # YouTube visitor tracking
    'YSC',                 # YouTube session cookie  
    'PREF',                # YouTube preferences
    'VISITOR_PRIVACY_METADATA',  # Privacy settings
]

AGE_RESTRICTED_COOKIES = [
    'LOGIN_INFO',          # Indicates logged-in status (needed for age-restricted)
]

# These provide full Google account access - AVOID IF POSSIBLE
DANGEROUS_COOKIES = [
    'SID',                 # Google account session
    'HSID',                # Google account secure session
    'SSID',                # Google account super secure session
    'APISID',              # API session ID
    'SAPISID',             # Secure API session ID
    '__Secure-1PAPISID',   # Secure API session
    '__Secure-3PAPISID',   # Secure API session
    '__Secure-1PSID',      # Secure session
    '__Secure-3PSID',      # Secure session
]

def print_security_warning():
    """Display security warning to user"""
    print("\n" + "="*70)
    print("⚠️  SECURITY WARNING ⚠️")
    print("="*70)
    print("""
YouTube cookies are part of your Google account authentication!
    
Risks of exporting cookies:
• These cookies can provide access to your Google account
• Anyone with these cookies can impersonate your YouTube session  
• Some cookies may grant access to other Google services

Recommendations:
✓ Use iOS/Android player clients instead of cookies when possible
✓ Create a dedicated Google account just for YouTube downloads
✓ Only export minimal cookies needed for your use case
✓ Rotate cookies frequently and monitor account activity
✓ Never share your cookie export with anyone
    """)
    print("="*70)
    
    response = input("\nDo you understand the security risks? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Exiting for your security. Please review the risks before proceeding.")
        sys.exit(0)

def get_chrome_cookies_db_path():
    """Get the path to Chrome's cookies database on macOS"""
    home = Path.home()
    chrome_paths = [
        home / "Library/Application Support/Google/Chrome/Default/Cookies",
        home / "Library/Application Support/Google/Chrome/Profile 1/Cookies",
        home / "Library/Application Support/Google/Chrome Beta/Default/Cookies",
        home / "Library/Application Support/Chromium/Default/Cookies",
    ]
    
    for path in chrome_paths:
        if path.exists():
            return path
    
    # Let user specify custom path
    custom_path = input("Chrome cookies not found. Enter path to Cookies file: ").strip()
    if custom_path and Path(custom_path).exists():
        return Path(custom_path)
    
    raise FileNotFoundError("Chrome cookies database not found")

def decrypt_cookie_value(encrypted_value):
    """Decrypt Chrome cookie value on macOS"""
    if not CRYPTO_AVAILABLE:
        return None
    
    if not encrypted_value or encrypted_value[:3] != b'v10':
        return encrypted_value.decode('utf-8', errors='ignore') if encrypted_value else ''
    
    try:
        # Get Chrome's encryption key from keychain
        import subprocess
        result = subprocess.run(
            ['security', 'find-generic-password', '-w', '-s', 'Chrome Safe Storage'],
            capture_output=True, text=True
        )
        password = result.stdout.strip()
        
        # Derive key using PBKDF2
        salt = b'saltysalt'
        key = Crypto.Protocol.KDF.PBKDF2(password.encode(), salt, 16, 1003)
        
        # Decrypt the cookie
        iv = b' ' * 16
        encrypted = encrypted_value[3:]
        cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)
        
        # Remove padding
        padding_length = decrypted[-1]
        if padding_length <= 16:
            decrypted = decrypted[:-padding_length]
        
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Warning: Could not decrypt cookie: {e}")
        return None

def extract_youtube_cookies(cookie_filter='minimal'):
    """Extract cookies for YouTube domains from Chrome
    
    Args:
        cookie_filter: 'minimal', 'age-restricted', or 'full'
    """
    cookies_db = get_chrome_cookies_db_path()
    
    # Copy database to temp file (Chrome locks the original)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        temp_db = tmp_file.name
        shutil.copy2(cookies_db, temp_db)
    
    # Determine which cookies to include
    if cookie_filter == 'minimal':
        allowed_cookies = ESSENTIAL_COOKIES
    elif cookie_filter == 'age-restricted':
        allowed_cookies = ESSENTIAL_COOKIES + AGE_RESTRICTED_COOKIES
    elif cookie_filter == 'full':
        allowed_cookies = None  # Include all cookies (DANGEROUS)
    else:
        allowed_cookies = ESSENTIAL_COOKIES
    
    cookies = []
    stats = {'total': 0, 'included': 0, 'excluded': 0}
    
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Query for YouTube cookies
        query = """
        SELECT host_key, name, value, encrypted_value, path, 
               expires_utc, is_secure, is_httponly, samesite
        FROM cookies 
        WHERE host_key LIKE '%youtube.com' 
           OR host_key LIKE '%.youtube.com'
        ORDER BY host_key, name
        """
        
        cursor.execute(query)
        
        for row in cursor.fetchall():
            host_key, name, value, encrypted_value, path, expires_utc, is_secure, is_httponly, samesite = row
            stats['total'] += 1
            
            # Filter cookies based on security level
            if allowed_cookies is not None and name not in allowed_cookies:
                stats['excluded'] += 1
                if name in DANGEROUS_COOKIES:
                    print(f"⚠️  Excluding dangerous cookie: {name}")
                continue
            
            # Try to get the cookie value
            if value:
                cookie_value = value
            elif encrypted_value and CRYPTO_AVAILABLE:
                cookie_value = decrypt_cookie_value(encrypted_value)
                if not cookie_value:
                    continue
            else:
                continue
            
            # Clean up cookie value - remove non-ASCII characters
            # YouTube cookies should be ASCII-safe
            try:
                # Try to encode as ASCII, replace problematic characters
                cookie_value = cookie_value.encode('ascii', 'ignore').decode('ascii')
            except:
                # Skip cookies with encoding issues
                print(f"⚠️  Skipping cookie with encoding issues: {name}")
                continue
            
            # Convert Chrome's microseconds since 1601 to Unix timestamp
            if expires_utc:
                # Chrome epoch starts at 1601-01-01
                expires = (expires_utc / 1000000) - 11644473600
            else:
                expires = 0
            
            # Create Netscape format cookie line
            # Format: domain flag path secure expiry name value
            domain = host_key if not host_key.startswith('.') else host_key
            flag = "TRUE" if host_key.startswith('.') else "FALSE"
            secure = "TRUE" if is_secure else "FALSE"
            
            cookie_line = f"{domain}\t{flag}\t{path}\t{secure}\t{int(expires)}\t{name}\t{cookie_value}"
            cookies.append(cookie_line)
            stats['included'] += 1
            print(f"✅ Including cookie: {name}")
        
        conn.close()
    finally:
        # Clean up temp file
        os.unlink(temp_db)
    
    return cookies, stats

def create_cookies_txt(cookies):
    """Create Netscape format cookies.txt content"""
    header = "# Netscape HTTP Cookie File\n"
    header += "# This file was generated by export_youtube_cookies.py\n"
    header += f"# Generated at: {datetime.now().isoformat()}\n"
    header += "# This is a generated file! Do not edit.\n"
    header += "# SECURITY: These are minimal YouTube cookies only.\n\n"
    
    content = header + "\n".join(cookies)
    return content

def main():
    parser = argparse.ArgumentParser(description='Export YouTube cookies from Chrome (Security-focused)')
    parser.add_argument('--level', choices=['minimal', 'age-restricted', 'full'],
                      default='minimal',
                      help='Cookie export level: minimal (safest), age-restricted, or full (dangerous)')
    parser.add_argument('--skip-warning', action='store_true',
                      help='Skip security warning (not recommended)')
    parser.add_argument('--output-dir', type=str, default=str(Path.home() / "Desktop"),
                      help='Output directory for cookie files')
    
    args = parser.parse_args()
    
    print("="*70)
    print("YouTube Cookie Exporter for yt-dlp API (Security-Focused)")
    print("="*70)
    print()
    
    # Show security warning unless skipped
    if not args.skip_warning:
        print_security_warning()
    
    print(f"\nExport level: {args.level.upper()}")
    if args.level == 'minimal':
        print("✅ Exporting only essential YouTube cookies (safest)")
    elif args.level == 'age-restricted':
        print("⚠️  Exporting cookies for age-restricted content")
    elif args.level == 'full':
        print("🚨 DANGEROUS: Exporting ALL cookies (includes Google account auth)")
    
    try:
        print("\nExtracting YouTube cookies from Chrome...")
        cookies, stats = extract_youtube_cookies(args.level)
        
        if not cookies:
            print("❌ No YouTube cookies found!")
            print("Make sure you're logged into YouTube in Chrome.")
            return
        
        print(f"\n📊 Cookie Statistics:")
        print(f"   Total found: {stats['total']}")
        print(f"   Included: {stats['included']}")
        print(f"   Excluded: {stats['excluded']}")
        
        # Create cookies.txt content
        cookies_txt = create_cookies_txt(cookies)
        
        # Save to file
        output_dir = Path(args.output_dir)
        output_file = output_dir / f"youtube_cookies_{args.level}.txt"
        output_file.write_text(cookies_txt)
        print(f"\n✅ Saved cookies to: {output_file}")
        
        # Create base64 version for environment variable
        cookies_base64 = base64.b64encode(cookies_txt.encode()).decode()
        
        # Save base64 to file for easy copying
        base64_file = output_dir / f"youtube_cookies_{args.level}_base64.txt"
        base64_file.write_text(cookies_base64)
        print(f"✅ Saved base64 version to: {base64_file}")
        
        print("\n" + "="*70)
        print("INSTRUCTIONS FOR RENDER.COM:")
        print("="*70)
        print(f"1. Open the file: youtube_cookies_{args.level}_base64.txt on your Desktop")
        print("2. Copy the entire content (it's one long line)")
        print("3. Go to your Render.com dashboard")
        print("4. Add environment variable: YOUTUBE_COOKIES_BASE64")
        print("5. Paste the copied content as the value")
        print("6. Save and deploy")
        print()
        print("⚠️  SECURITY REMINDERS:")
        print("• These cookies expire in about 2 weeks")
        print("• Re-run this script when you need to update them")
        print("• Monitor your Google account for unauthorized access")
        print("• Consider using a dedicated YouTube account for downloads")
        
        # Also save a local cookies file for testing
        local_cookies = Path("cookies.txt")
        local_cookies.write_text(cookies_txt)
        print(f"\n✅ Also saved local cookies.txt for testing")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()