#!/usr/bin/env python3
import sys, os, re, json, time, requests
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import m3u8

class URLValidator:
    @staticmethod
    def is_valid(url):
        if not url:
            return False
        return bool(re.match(r'^https?://(www\.)?khdiamond\.net/movies/.*$', url, re.IGNORECASE))

class PageScraper:
    def __init__(self, session):
        self.session = session
    def get_metadata(self, url):
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Video"
        manifest_url = None
        video = soup.find('video')
        if video and video.get('src'):
            manifest_url = video.get('src')
        if not manifest_url:
            source = soup.find('source')
            if source and source.get('src'):
                manifest_url = source.get('src')
        if not manifest_url:
            for script in soup.find_all('script'):
                if script.string:
                    matches = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', script.string)
                    if matches:
                        manifest_url = matches[0]
                        break
        return {'title': title, 'manifest_url': manifest_url}

class StreamHandler:
    def __init__(self, session):
        self.session = session
    def get_qualities(self, manifest_url):
        try:
            resp = self.session.get(manifest_url, timeout=10)
            resp.raise_for_status()
            playlist = m3u8.loads(resp.text)
            qualities = []
            if playlist.is_variant:
                for v in playlist.playlists:
                    bw = v.stream_info.bandwidth
                    label = "1080p" if bw > 3000000 else "720p" if bw > 1500000 else "480p" if bw > 800000 else "360p"
                    qualities.append({'label': label, 'url': v.uri, 'bandwidth': bw})
            else:
                qualities.append({'label': 'Auto', 'url': manifest_url, 'bandwidth': 0})
            qualities.sort(key=lambda x: x.get('bandwidth', 0))
            return qualities
        except:
            return []

class DownloadEngine:
    def __init__(self, session):
        self.session = session
    def format_time(self, s):
        return f"{int(s//60)}m {int(s%60)}s" if s >= 60 else f"{s:.0f}s"
    def download(self, url, filepath, progress_callback=None):
        try:
            resp = self.session.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            total = int(resp.headers.get('content-length', 0))
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            downloaded, start, last = 0, time.time(), 0
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last > 0.5:
                            elapsed = now - start
                            speed = (downloaded/1024)/elapsed if elapsed > 0 else 0
                            remaining = (total - downloaded)/(speed*1024) if speed > 0 and total > 0 else 0
                            percent = (downloaded/total*100) if total > 0 else 0
                            if progress_callback:
                                progress_callback(percent, speed, self.format_time(remaining), downloaded/(1024*1024), total/(1024*1024))
                            last = now
            return True
        except:
            return False

class App:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.save_path = Path.home() / 'Downloads'
        self.save_path.mkdir(exist_ok=True)

    def run(self):
        while True:
            os.system('clear')
            print("\033[1;36m" + "="*60 + "\033[0m")
            print("\033[1;33m  KHDIAMOND DOWNLOADER v1.0\033[0m")
            print("\033[1;36m" + "="*60 + "\033[0m")
            print("  Supported: khdiamond.net/movies\n")
            url = input("\033[1;32m>> Paste URL: \033[0m").strip()
            if not url:
                print("\nGoodbye!")
                break
            if not URLValidator.is_valid(url):
                print("\033[1;31mInvalid URL!\033[0m")
                input("Press Enter to continue...")
                continue
            print("\n\033[1;34mAnalyzing...\033[0m")
            try:
                scraper = PageScraper(self.session)
                meta = scraper.get_metadata(url)
                if not meta or not meta['manifest_url']:
                    print("\033[1;31mNo manifest found.\033[0m")
                    input("Press Enter...")
                    continue
                handler = StreamHandler(self.session)
                qualities = handler.get_qualities(meta['manifest_url'])
                if not qualities:
                    print("\033[1;31mNo qualities found.\033[0m")
                    input("Press Enter...")
                    continue
                print(f"\n\033[1;37mTitle: \033[1;33m{meta['title']}\033[0m")
                print("\n\033[1;37mQualities:\033[0m")
                for i, q in enumerate(qualities, 1):
                    print(f"  \033[1;33m[{i}]\033[0m {q['label']}")
                print("  \033[1;33m[0]\033[0m Cancel")
                choice = input("\n\033[1;32mSelect: \033[0m").strip()
                if choice == '0':
                    continue
                try:
                    idx = int(choice) - 1
                    if idx < 0 or idx >= len(qualities):
                        print("\033[1;31mInvalid.\033[0m")
                        input("Press Enter...")
                        continue
                    selected = qualities[idx]
                except:
                    print("\033[1;31mInvalid.\033[0m")
                    input("Press Enter...")
                    continue
                safe_title = "".join(c for c in meta['title'] if c.isalnum() or c in ' -_').strip()
                filename = f"{safe_title}.mp4"
                filepath = self.save_path / filename
                print(f"\n\033[1;34mDownloading to: {filepath}\033[0m")
                print("\033[1;36m" + "-"*60 + "\033[0m")
                engine = DownloadEngine(self.session)
                def progress(percent, speed, eta, downloaded, total):
                    bar = '█' * int(40 * percent / 100) + '░' * (40 - int(40 * percent / 100))
                    sys.stdout.write(f'\r\033[1;32m[{bar}]\033[0m {percent:.1f}%  {downloaded:.1f}MB/{total:.1f}MB  {speed:.1f}KB/s  ETA: {eta}')
                    sys.stdout.flush()
                success = engine.download(selected['url'], str(filepath), progress)
                if success:
                    print("\n\n\033[1;32m✅ Download complete!\033[0m")
                    print(f"   Saved to: \033[1;37m{filepath}\033[0m")
                else:
                    print("\n\033[1;31m❌ Download failed.\033[0m")
            except Exception as e:
                print(f"\033[1;31mError: {e}\033[0m")
            again = input("\n\033[1;37mDownload another? (y/n): \033[0m").strip().lower()
            if again != 'y':
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    App().run()
