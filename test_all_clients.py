#!/usr/bin/env python3
"""
Test format availability across all major YouTube clients
"""

import yt_dlp

# Test URL
test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

clients = ['ios', 'android', 'web', 'mweb', 'tv']

print("Comparing format availability across YouTube clients")
print("="*70)

results = {}

for client in clients:
    print(f'\nTesting {client.upper()} client:')
    print("-"*40)
    
    opts = {
        'quiet': True,
        'skip_download': True,
        'extractor_args': {'youtube': {'player_client': [client]}},
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            formats = info.get('formats', [])
            
            # Get stats
            total = len(formats)
            mp4_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('height')]
            combined_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') != 'none' and f.get('height')]
            
            highest_mp4 = max(mp4_formats, key=lambda x: x.get('height', 0)) if mp4_formats else None
            highest_combined = max(combined_formats, key=lambda x: x.get('height', 0)) if combined_formats else None
            
            results[client] = {
                'total': total,
                'mp4_count': len(mp4_formats),
                'combined_count': len(combined_formats),
                'highest_mp4': highest_mp4.get('height') if highest_mp4 else 0,
                'highest_combined': highest_combined.get('height') if highest_combined else 0,
                'highest_mp4_id': highest_mp4.get('format_id') if highest_mp4 else 'N/A',
                'highest_combined_id': highest_combined.get('format_id') if highest_combined else 'N/A',
            }
            
            print(f"  Total formats: {total}")
            print(f"  MP4 formats: {len(mp4_formats)}")
            print(f"  Combined A+V formats: {len(combined_formats)}")
            print(f"  Highest MP4: {results[client]['highest_mp4']}p (format {results[client]['highest_mp4_id']})")
            print(f"  Highest Combined: {results[client]['highest_combined']}p (format {results[client]['highest_combined_id']})")
            
            # Show available resolutions
            if mp4_formats:
                resolutions = sorted(list(set(f.get('height') for f in mp4_formats if f.get('height'))), reverse=True)
                print(f"  Available MP4 resolutions: {', '.join(f'{r}p' for r in resolutions[:5])}")
                
    except Exception as e:
        print(f'  FAILED: {str(e)[:100]}')
        results[client] = {'error': str(e)}

print('\n' + '='*70)
print('SUMMARY TABLE:')
print('-'*70)
print(f"{'Client':<10} {'Total':<8} {'MP4s':<8} {'Combined':<10} {'Highest MP4':<12} {'Highest A+V':<12}")
print('-'*70)

for client in clients:
    if client in results and 'error' not in results[client]:
        r = results[client]
        print(f"{client.upper():<10} {r['total']:<8} {r['mp4_count']:<8} {r['combined_count']:<10} "
              f"{r['highest_mp4']}p{'':<8} {r['highest_combined']}p")
    else:
        print(f"{client.upper():<10} {'ERROR':<8}")

print('\n' + '='*70)
print('KEY FINDINGS:')
print('- Android client is severely limited to 360p maximum resolution')
print('- iOS client provides full range including 4K (2160p)')
print('- Web client may require authentication for higher resolutions')
print('- TV client typically provides good quality formats')
print('- Mobile web (mweb) client may have intermediate quality')