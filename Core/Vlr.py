import re

ALLOWED_DOMAINS = ['khdiamond.net', 'www.khdiamond.net']

class URLValidator:
    @staticmethod
    def is_valid(url):
        """Validate if URL is from allowed domain"""
        if not url:
            return False
        
        # Basic URL pattern
        pattern = r'^https?://(www\.)?khdiamond\.net/movies/.*$'
        if not re.match(pattern, url, re.IGNORECASE):
            return False
        
        # Additional check for allowed domains
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain in ALLOWED_DOMAINS
