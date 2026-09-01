#!/usr/bin/env python3
"""
KHDiamond Downloader - Simple Terminal Video Downloader
Author: Bread & Sonion
License: Educational/Personal Use Only
"""

import sys
import os
import json
from pathlib import Path
from core.validator import URLValidator
from core.scraper import PageScraper
from core.stream import StreamHandler
from core.downloader import DownloadEngine
from core.config import ConfigManager
import requests

class KHDiamondCLI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.config = ConfigManager.load()
        self.running = True

    def clear_screen(self):
        """Clear terminal for better UX"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print_header(self):
        """Display application header"""
        print("\033[1;36m" + "═" * 60 + "\033[0m")
        print("\033[1;33m" + "  🎬 KHDIAMOND DOWNLOADER v1.0" + "\033[0m")
        print("\033[1;36m" + "═" * 60 + "\033[0m")
        print("  Simple • Fast • Terminal-Based")
        print("  Supported: khdiamond.net/movies")
        print("\033[1;36m" + "═" * 60 + "\033[0m\n")

    def get_url(self):
        """Prompt user for video URL"""
        print("\033[1;37m📌 Paste Video URL:\033[0m")
        print("   (Example: https://khdiamond.net/movies/awesome-movie)")
        url = input("\033[1;32m➜ \033[0m").strip()
        return url

    def analyze_video(self, url):
        """Analyze the video URL and extract metadata"""
        print("\n\033[1;34m🔍 Analyzing video...\033[0m")
        
        # Validate URL
        if not URLValidator.is_valid(url):
            print("\033[1;31m❌ Invalid URL! Only khdiamond.net/movies allowed.\033[0m")
            return None

        try:
            # Scrape page
            scraper = PageScraper(self.session)
            metadata = scraper.get_metadata(url)
            
            if not metadata or not metadata.get('manifest_url'):
                print("\033[1;31m❌ No video manifest found on this page.\033[0m")
                return None

            # Get available qualities
            stream_handler = StreamHandler(self.session)
            qualities = stream_handler.get_qualities(metadata['manifest_url'])
            
            if not qualities:
                print("\033[1;31m❌ No downloadable qualities found.\033[0m")
                return None

            return {
                'title': metadata['title'],
                'qualities': qualities,
                'manifest_url': metadata['manifest_url']
            }

        except requests.exceptions.RequestException as e:
            print(f"\033[1;31m❌ Network error: {str(e)}\033[0m")
            return None
        except Exception as e:
            print(f"\033[1;31m❌ Error analyzing video: {str(e)}\033[0m")
            return None

    def display_qualities(self, qualities):
        """Display available quality options"""
        print("\n\033[1;37m🎬 Available Qualities:\033[0m")
        for idx, q in enumerate(qualities, 1):
            label = q.get('label', f"{q.get('height', 'Unknown')}p")
            print(f"  \033[1;33m[{idx}]\033[0m {label}")
        print("  \033[1;33m[0]\033[0m Cancel")

    def select_quality(self, qualities):
        """Prompt user to select a quality"""
        while True:
            try:
                choice = input("\n\033[1;32m➜ Select quality (0 to cancel): \033[0m").strip()
                if choice == '0':
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(qualities):
                    return qualities[idx]
                print("\033[1;31m❌ Invalid selection. Please try again.\033[0m")
            except ValueError:
                print("\033[1;31m❌ Please enter a number.\033[0m")

    def download_video(self, quality, title):
        """Download the selected video quality"""
        save_path = self.config.get('save_path', str(Path.home() / 'Downloads'))
        
        # Ensure save directory exists
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.mp4"
        filepath = Path(save_path) / filename

        print(f"\n\033[1;34m📥 Downloading: {title}\033[0m")
        print(f"   📁 Save location: {filepath}")
        print(f"   📊 Quality: {quality.get('label', 'Unknown')}")
        print("\n\033[1;36m" + "─" * 60 + "\033[0m")

        # Initialize download engine
        engine = DownloadEngine(self.session)
        
        def progress_callback(percent, speed, eta, downloaded, total):
            # Clear line and print progress
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            sys.stdout.write('\r')
            sys.stdout.write(f"\033[1;32m[{bar}]\033[0m {percent:.1f}%  ")
            sys.stdout.write(f"📊 {downloaded:.2f}MB / {total:.2f}MB  ")
            sys.stdout.write(f"⚡ {speed:.2f} KB/s  ")
            sys.stdout.write(f"⏱️  {eta}")
            sys.stdout.flush()

        try:
            success = engine.download(
                url=quality['url'],
                filepath=str(filepath),
                progress_callback=progress_callback
            )
            
            if success:
                print("\n\n\033[1;32m✅ Download complete!\033[0m")
                print(f"   📁 Saved to: \033[1;37m{filepath}\033[0m")
                return True
            else:
                print("\n\033[1;31m❌ Download failed.\033[0m")
                return False

        except KeyboardInterrupt:
            print("\n\n\033[1;33m⚠️ Download interrupted by user.\033[0m")
            return False
        except Exception as e:
            print(f"\n\033[1;31m❌ Download error: {str(e)}\033[0m")
            return False

    def ask_continue(self):
        """Ask user if they want to download another video"""
        print("\n" + "─" * 60)
        choice = input("\n\033[1;37m📥 Download another video? (y/n): \033[0m").strip().lower()
        return choice == 'y' or choice == 'yes'

    def run(self):
        """Main application loop"""
        try:
            while self.running:
                self.clear_screen()
                self.print_header()
                
                # Get URL
                url = self.get_url()
                if not url:
                    print("\n\033[1;33m⚠️ No URL provided. Exiting...\033[0m")
                    break

                # Analyze video
                video_info = self.analyze_video(url)
                if not video_info:
                    if not self.ask_continue():
                        break
                    continue

                # Display video title
                print(f"\n\033[1;37m🎬 Title: \033[1;33m{video_info['title']}\033[0m")

                # Display and select quality
                self.display_qualities(video_info['qualities'])
                selected_quality = self.select_quality(video_info['qualities'])
                
                if not selected_quality:
                    print("\n\033[1;33m⏹️ Download cancelled.\033[0m")
                    if not self.ask_continue():
                        break
                    continue

                # Download video
                success = self.download_video(selected_quality, video_info['title'])
                
                # Ask to continue or exit
                if not self.ask_continue():
                    break

        except KeyboardInterrupt:
            print("\n\n\033[1;33m👋 Goodbye!\033[0m")
            sys.exit(0)
        except Exception as e:
            print(f"\n\033[1;31m❌ Fatal error: {str(e)}\033[0m")
            sys.exit(1)

if __name__ == "__main__":
    cli = KHDiamondCLI()
    cli.run()            # Scrape page
            scraper = PageScraper(self.session)
            metadata = scraper.get_metadata(url)
            
            if not metadata or not metadata.get('manifest_url'):
                print("\033[1;31m❌ No video manifest found on this page.\033[0m")
                return None

            # Get available qualities
            stream_handler = StreamHandler(self.session)
            qualities = stream_handler.get_qualities(metadata['manifest_url'])
            
            if not qualities:
                print("\033[1;31m❌ No downloadable qualities found.\033[0m")
                return None

            return {
                'title': metadata['title'],
                'qualities': qualities,
                'manifest_url': metadata['manifest_url']
            }

        except requests.exceptions.RequestException as e:
            print(f"\033[1;31m❌ Network error: {str(e)}\033[0m")
            return None
        except Exception as e:
            print(f"\033[1;31m❌ Error analyzing video: {str(e)}\033[0m")
            return None

    def display_qualities(self, qualities):
        """Display available quality options"""
        print("\n\033[1;37m🎬 Available Qualities:\033[0m")
        for idx, q in enumerate(qualities, 1):
            label = q.get('label', f"{q.get('height', 'Unknown')}p")
            print(f"  \033[1;33m[{idx}]\033[0m {label}")
        print("  \033[1;33m[0]\033[0m Cancel")

    def select_quality(self, qualities):
        """Prompt user to select a quality"""
        while True:
            try:
                choice = input("\n\033[1;32m➜ Select quality (0 to cancel): \033[0m").strip()
                if choice == '0':
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(qualities):
                    return qualities[idx]
                print("\033[1;31m❌ Invalid selection. Please try again.\033[0m")
            except ValueError:
                print("\033[1;31m❌ Please enter a number.\033[0m")

    def download_video(self, quality, title):
        """Download the selected video quality"""
        save_path = self.config.get('save_path', str(Path.home() / 'Downloads'))
        
        # Ensure save directory exists
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.mp4"
        filepath = Path(save_path) / filename

        print(f"\n\033[1;34m📥 Downloading: {title}\033[0m")
        print(f"   📁 Save location: {filepath}")
        print(f"   📊 Quality: {quality.get('label', 'Unknown')}")
        print("\n\033[1;36m" + "─" * 60 + "\033[0m")

        # Initialize download engine
        engine = DownloadEngine(self.session)
        
        def progress_callback(percent, speed, eta, downloaded, total):
            # Clear line and print progress
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            sys.stdout.write('\r')
            sys.stdout.write(f"\033[1;32m[{bar}]\033[0m {percent:.1f}%  ")
            sys.stdout.write(f"📊 {downloaded:.2f}MB / {total:.2f}MB  ")
            sys.stdout.write(f"⚡ {speed:.2f} KB/s  ")
            sys.stdout.write(f"⏱️  {eta}")
            sys.stdout.flush()

        try:
            success = engine.download(
                url=quality['url'],
                filepath=str(filepath),
                progress_callback=progress_callback
            )
            
            if success:
                print("\n\n\033[1;32m✅ Download complete!\033[0m")
                print(f"   📁 Saved to: \033[1;37m{filepath}\033[0m")
                return True
            else:
                print("\n\033[1;31m❌ Download failed.\033[0m")
                return False

        except KeyboardInterrupt:
            print("\n\n\033[1;33m⚠️ Download interrupted by user.\033[0m")
            return False
        except Exception as e:
            print(f"\n\033[1;31m❌ Download error: {str(e)}\033[0m")
            return False

    def ask_continue(self):
        """Ask user if they want to download another video"""
        print("\n" + "─" * 60)
        choice = input("\n\033[1;37m📥 Download another video? (y/n): \033[0m").strip().lower()
        return choice == 'y' or choice == 'yes'

    def run(self):
        """Main application loop"""
        try:
            while self.running:
                self.clear_screen()
                self.print_header()
                
                # Get URL
                url = self.get_url()
                if not url:
                    print("\n\033[1;33m⚠️ No URL provided. Exiting...\033[0m")
                    break

                # Analyze video
                video_info = self.analyze_video(url)
                if not video_info:
                    if not self.ask_continue():
                        break
                    continue

                # Display video title
                print(f"\n\033[1;37m🎬 Title: \033[1;33m{video_info['title']}\033[0m")

                # Display and select quality
                self.display_qualities(video_info['qualities'])
                selected_quality = self.select_quality(video_info['qualities'])
                
                if not selected_quality:
                    print("\n\033[1;33m⏹️ Download cancelled.\033[0m")
                    if not self.ask_continue():
                        break
                    continue

                # Download video
                success = self.download_video(selected_quality, video_info['title'])
                
                # Ask to continue or exit
                if not self.ask_continue():
                    break

        except KeyboardInterrupt:
            print("\n\n\033[1;33m👋 Goodbye!\033[0m")
            sys.exit(0)
        except Exception as e:
            print(f"\n\033[1;31m❌ Fatal error: {str(e)}\033[0m")
            sys.exit(1)

if __name__ == "__main__":
    cli = KHDiamondCLI()
    cli.run()
