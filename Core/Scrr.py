import re
from bs4 import BeautifulSoup

class PageScraper:
    def __init__(self, session):
        self.session = session

    def get_metadata(self, url):
        """Extract video title and manifest URL from page"""
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract title
        title = "Unknown Video"
        title_tag = soup.find('h1')
        if title_tag:
            title = title_tag.text.strip()
        
        # Find video source - multiple strategies
        manifest_url = None
        
        # Strategy 1: Check video tag
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            manifest_url = video_tag.get('src')
        
        # Strategy 2: Check source tags
        if not manifest_url:
            source = soup.find('source')
            if source and source.get('src'):
                manifest_url = source.get('src')
        
        # Strategy 3: Check iframes (for embedded players)
        if not manifest_url:
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                # Look for common video hosting patterns
                if 'dood' in src or 'streamtape' in src or 'mixdrop' in src:
                    # We'd need to scrape the iframe source for direct manifest
                    # For simplicity, we'll note this for future expansion
                    manifest_url = src
        
        # Strategy 4: Check for m3u8 in script tags or meta
        if not manifest_url:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for .m3u8 URLs
                    matches = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', script.string)
                    if matches:
                        manifest_url = matches[0]
                        break
        
        return {
            'title': title,
            'manifest_url': manifest_url
        }
