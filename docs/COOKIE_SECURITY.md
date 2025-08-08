# YouTube Cookie Security Guide

## ⚠️ CRITICAL SECURITY INFORMATION

**YouTube cookies are NOT isolated from your Google account!** They provide authentication to your entire Google ecosystem.

## Understanding the Risk

### What YouTube Cookies Actually Are

YouTube cookies are part of Google's unified authentication system. Key cookies include:

1. **Session Cookies (HIGH RISK)**
   - `SID`, `HSID`, `SSID` - Google account session identifiers
   - `SAPISID`, `APISID` - API authentication tokens
   - These provide access to ALL Google services (Gmail, Drive, Calendar, etc.)

2. **YouTube-Specific Cookies (LOWER RISK)**
   - `VISITOR_INFO1_LIVE` - YouTube visitor tracking
   - `YSC` - YouTube session cookie
   - `PREF` - YouTube preferences
   - These are primarily for YouTube functionality

3. **Login Status Cookies (MEDIUM RISK)**
   - `LOGIN_INFO` - Indicates logged-in status
   - Required for age-restricted content
   - Can reveal account association

### The Security Problem

Google uses a **centralized authentication system** where:
- All Google services share the same authentication cookies
- YouTube.com, Gmail.com, Drive.google.com all trust the same session tokens
- **Anyone with your YouTube cookies can potentially access your entire Google account**

## Risk Assessment

### What Can Happen If Cookies Are Compromised

1. **Session Hijacking** - Attacker can impersonate your Google session
2. **Account Access** - Potential access to Gmail, Drive, Calendar, Photos
3. **Data Exposure** - Personal emails, documents, photos could be accessed
4. **Persistence** - Cookies can remain valid for weeks
5. **Bypass 2FA** - Session cookies bypass two-factor authentication

### Real Attack Scenarios

- **2024 Info-Stealer Campaigns**: Malware specifically targets Google session cookies
- **Cookie Theft Attacks**: Phishing campaigns targeting YouTube creators
- **Persistent Access**: Attackers maintain access even after password changes

## Recommended Security Practices

### 1. Use Alternative Methods First

**Priority Order:**
1. **iOS/Android Player Clients** - No authentication needed
2. **Dedicated YouTube Account** - Separate account just for downloads
3. **Minimal Cookie Export** - Only essential cookies
4. **Full Cookie Export** - Last resort, highest risk

### 2. If You Must Use Cookies

#### Create a Dedicated YouTube Account
```bash
1. Create new Google account specifically for YouTube downloads
2. Don't use this account for any sensitive services
3. Don't link it to your phone number or recovery email
4. Use this account's cookies for the API
```

#### Use Minimal Cookie Export
```bash
# Export only essential cookies (safest)
python3 export_youtube_cookies.py --level minimal

# For age-restricted content
python3 export_youtube_cookies.py --level age-restricted

# AVOID: Full export (includes all Google auth)
python3 export_youtube_cookies.py --level full  # DANGEROUS
```

### 3. Security Best Practices

1. **Rotate Frequently**
   - Cookies expire in ~2 weeks
   - Rotate weekly for better security
   - Monitor Google account activity

2. **Secure Storage**
   - Never commit cookies to git
   - Use environment variables only
   - Don't share cookie exports

3. **Monitor Account**
   - Check Google Account activity regularly
   - Enable security alerts
   - Review connected devices

4. **Revoke Access If Compromised**
   - Sign out of all sessions
   - Change password immediately
   - Review account permissions

## Cookie Types Explained

### Minimal Export (Recommended)
Only includes:
- `VISITOR_INFO1_LIVE` - Basic YouTube tracking
- `YSC` - YouTube session
- `PREF` - Preferences
- `VISITOR_PRIVACY_METADATA` - Privacy settings

**Use Case**: Basic video downloads, public content

### Age-Restricted Export
Adds:
- `LOGIN_INFO` - Logged-in status indicator

**Use Case**: Age-restricted videos, member-only content

### Full Export (DANGEROUS)
Includes ALL cookies including:
- `SID`, `HSID`, `SSID` - Full Google account session
- `SAPISID`, `APISID` - API authentication
- `__Secure-*` cookies - Enhanced security tokens

**Risk**: Full Google account access
**Recommendation**: AVOID unless absolutely necessary

## How to Check What's Exported

```bash
# View which cookies will be exported
python3 export_youtube_cookies.py --level minimal

# Output shows:
✅ Including cookie: VISITOR_INFO1_LIVE
✅ Including cookie: YSC
⚠️  Excluding dangerous cookie: SID
⚠️  Excluding dangerous cookie: HSID
```

## Emergency Response

### If Cookies Are Compromised

1. **Immediately**:
   ```
   Go to: https://myaccount.google.com/security
   → Sign out of all other sessions
   → Change password
   ```

2. **Review Activity**:
   ```
   Check: https://myaccount.google.com/activitycontrols
   → Review recent activity
   → Look for unauthorized access
   ```

3. **Revoke Tokens**:
   ```
   Visit: https://myaccount.google.com/permissions
   → Remove suspicious apps
   → Reset all app passwords
   ```

## Technical Details

### Cookie Scope
- YouTube cookies domain: `.youtube.com`
- But they authenticate via: `accounts.google.com`
- Cross-origin requests share authentication

### yt-dlp Cookie Usage
yt-dlp primarily uses:
- `SAPISID` for API authentication (if available)
- `LOGIN_INFO` to check logged-in status
- `VISITOR_INFO1_LIVE` for tracking

### API Fallback Strategy
```
1. Try iOS client (no cookies needed) ← PREFERRED
2. Try minimal cookies (if configured)
3. Try Android client (limited quality)
4. Fail with clear error message
```

## Recommendations

### For Maximum Security
1. **Don't use cookies** - Stick to iOS/Android clients
2. **Use dedicated account** - Separate YouTube account for downloads
3. **Export minimal** - Only essential cookies
4. **Rotate frequently** - Weekly rotation
5. **Monitor actively** - Check account activity

### For Developers
1. Default to iOS client in code
2. Make cookie support optional
3. Add clear security warnings
4. Log which method succeeds
5. Don't store cookies in code

## Alternative Solutions

### 1. Browser Extensions (Controlled Export)
- "Get cookies.txt LOCALLY" - Allows selective export
- Can filter by domain before export
- Manual control over what's included

### 2. OAuth2 YouTube Plugin
- Uses proper OAuth flow
- Scoped permissions
- No session cookie exposure
- More complex setup

### 3. Public Proxies/Instances
- Use public yt-dlp instances
- No authentication needed
- Limited to public content
- Performance varies

## Conclusion

YouTube cookies are **Google account cookies**. They provide broader access than just YouTube. Always prefer authentication-free methods (iOS/Android clients) and use cookies only as a last resort with a dedicated account.

**Remember**: The convenience of cookie authentication comes with significant security risks. Make informed decisions based on your threat model and the sensitivity of your Google account data.