import requests
import time
import os
import math
from pathlib import Path

class DownloadEngine:
    def __init__(self, session):
        self.session = session
        self.last_speed_update = 0
        self.last_bytes = 0

    def format_size(self, bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

    def format_time(self, seconds):
        """Convert seconds to human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def download(self, url, filepath, progress_callback=None):
        """Download file with progress tracking"""
        try:
            # Handle relative URLs
            if not url.startswith('http'):
                # Build absolute URL from base
                base = '/'.join(url.split('/')[:-1]) + '/'
                if not url.startswith('/'):
                    url = base + url
            
            # Start download
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            
            # Prepare file
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            downloaded = 0
            start_time = time.time()
            last_update = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress every 0.5 seconds
                        current_time = time.time()
                        if current_time - last_update > 0.5:
                            # Calculate speed
                            elapsed = current_time - start_time
                            speed = (downloaded / 1024) / elapsed if elapsed > 0 else 0  # KB/s
                            
                            # Calculate ETA
                            if speed > 0 and total_size > 0:
                                remaining = (total_size - downloaded) / (speed * 1024)
                                eta = self.format_time(remaining)
                            else:
                                eta = "Calculating..."
                            
                            # Calculate percentage
                            percent = (downloaded / total_size * 100) if total_size > 0 else 0
                            
                            # Format sizes
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            # Call progress callback
                            if progress_callback:
                                progress_callback(percent, speed, eta, downloaded_mb, total_mb)
                            
                            last_update = current_time
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Download error: {e}")
            return False
