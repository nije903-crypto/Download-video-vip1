import m3u8

class StreamHandler:
    def __init__(self, session):
        self.session = session

    def get_qualities(self, manifest_url):
        """Extract available video qualities from manifest"""
        try:
            resp = self.session.get(manifest_url, timeout=10)
            resp.raise_for_status()
            
            playlist = m3u8.loads(resp.text)
            qualities = []
            
            # If it's a master playlist with variants
            if playlist.is_variant:
                for variant in playlist.playlists:
                    bandwidth = variant.stream_info.bandwidth
                    # Determine quality label
                    if bandwidth < 500000:
                        label = "360p"
                    elif bandwidth < 1000000:
                        label = "480p"
                    elif bandwidth < 2000000:
                        label = "720p"
                    elif bandwidth < 4000000:
                        label = "1080p"
                    else:
                        label = f"{bandwidth//1000}k"
                    
                    qualities.append({
                        'label': label,
                        'url': variant.uri,
                        'bandwidth': bandwidth
                    })
            else:
                # Single quality manifest
                qualities.append({
                    'label': 'Auto',
                    'url': manifest_url,
                    'bandwidth': 0
                })
            
            # Sort by bandwidth (lowest to highest)
            qualities.sort(key=lambda x: x.get('bandwidth', 0))
            return qualities
            
        except Exception as e:
            print(f"Error parsing manifest: {e}")
            return []
