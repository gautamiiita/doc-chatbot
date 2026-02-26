#!/usr/bin/env python3
"""
Web-based Confluence Crawler
Scrapes the HTML to extract all pages from the Release Notes hierarchy
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from html.parser import HTMLParser
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
import logging
from dotenv import load_dotenv
import os
import time

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML"""
    
    def __init__(self):
        super().__init__()
        self.text = []
        
    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'div', 'li']:
            self.text.append("\n")
        elif tag in ['h1', 'h2', 'h3', 'h4']:
            self.text.append("\n## ")
        elif tag == 'br':
            self.text.append("\n")
            
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)
            
    def get_text(self) -> str:
        text = " ".join(self.text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

class WebConfluenceCrawler:
    """Crawl Confluence by scraping HTML"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.pages = {}
        self.seen_urls: Set[str] = set()
        self.pages_fetched = 0
        
        # Basic auth if provided
        if username and password:
            self.session.auth = (username, password)
    
    def extract_text(self, html_content: str) -> str:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get main content area
            content = soup.find('main')
            if not content:
                content = soup.find('article')
            if not content:
                content = soup.find('div', class_='wiki-content')
            if not content:
                content = soup
            
            # Extract text
            extractor = HTMLTextExtractor()
            extractor.feed(str(content))
            return extractor.get_text()
            
        except Exception as e:
            logger.warning(f"Error extracting text: {str(e)}")
            return ""
    
    def get_page_title(self, html_content: str) -> str:
        """Extract page title from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try different title selectors
            title = soup.find('h1', class_='page-title')
            if title:
                return title.get_text(strip=True)
            
            title = soup.find('title')
            if title:
                text = title.get_text(strip=True)
                # Remove trailing "Confluence" or "- Secutix"
                text = re.sub(r'\s*[\|-].*', '', text)
                return text
            
            return "Unknown"
        except:
            return "Unknown"
    
    def extract_links_from_page(self, html_content: str, page_url: str) -> List[str]:
        """Extract all Release Notes related links from a page"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            links = []
            seen = set()
            
            # Look for the Release Notes navigation or content links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '')
                
                # Only follow Confluence page links
                if '/wiki/' not in href or '/pages/' not in href:
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                else:
                    full_url = urljoin(page_url, href)
                
                # Normalize (remove query params)
                full_url = re.sub(r'\?.*$', '', full_url)
                
                # Only crawl confluence-secutix.atlassian.net
                if 'confluence-secutix.atlassian.net' not in full_url:
                    continue
                
                # Skip if already seen
                if full_url in seen:
                    continue
                
                seen.add(full_url)
                links.append(full_url)
            
            return links
            
        except Exception as e:
            logger.warning(f"Error extracting links: {str(e)}")
            return []
    
    def fetch_page(self, url: str, timeout: int = 15) -> Dict:
        """Fetch a page and extract info"""
        
        if url in self.seen_urls:
            return None
        
        self.seen_urls.add(url)
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
            
            # Extract info
            title = self.get_page_title(response.text)
            text = self.extract_text(response.text)
            
            # Skip very short pages (probably navigation or errors)
            if len(text) < 100:
                logger.debug(f"Skipping (too short): {title}")
                return None
            
            # Extract page ID from URL
            page_id_match = re.search(r'pageId=(\d+)', url)
            page_id = page_id_match.group(1) if page_id_match else url.split('/')[-1]
            
            page_info = {
                'id': page_id,
                'title': title,
                'url': url,
                'text': text,
                'text_size': len(text),
            }
            
            self.pages[page_id] = page_info
            self.pages_fetched += 1
            
            logger.info(f"  ✓ {title[:60]} ({len(text)} chars)")
            
            return page_info
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def crawl_release_notes(self, start_url: str = "https://confluence-secutix.atlassian.net/wiki/spaces/RN/overview", max_pages: int = 500):
        """Crawl Release Notes pages"""
        logger.info(f"Starting web crawl from: {start_url}")
        
        to_visit = [start_url]
        visited = set()
        
        while to_visit and self.pages_fetched < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            visited.add(url)
            
            # Fetch page
            page_data = self.fetch_page(url)
            if not page_data:
                continue
            
            # Extract links from this page
            response = self.session.get(url, timeout=15)
            new_links = self.extract_links_from_page(response.text, url)
            
            # Add new links to visit queue
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)
            
            # Rate limiting
            time.sleep(0.5)
        
        logger.info(f"\n✅ Crawl complete: {self.pages_fetched} pages fetched")
        return list(self.pages.values())
    
    def save_pages(self, pages: List[Dict], filename: str = "confluence_pages.json"):
        """Save crawled pages"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved {len(pages)} pages to {filename}")
            
            total_chars = sum(p['text_size'] for p in pages)
            logger.info(f"\n📊 Statistics:")
            logger.info(f"   Total pages: {len(pages)}")
            logger.info(f"   Total content: {total_chars:,} characters (~{total_chars//1024}KB)")
            logger.info(f"   Avg page size: {total_chars//len(pages) if pages else 0:,} chars")
            
        except Exception as e:
            logger.error(f"Error saving pages: {str(e)}")

def main():
    """Main entry point"""
    
    username = os.getenv("CONFLUENCE_USERNAME")
    password = os.getenv("CONFLUENCE_API_TOKEN")
    
    # Create crawler
    crawler = WebConfluenceCrawler(
        "https://confluence-secutix.atlassian.net",
        username=username,
        password=password
    )
    
    # Start from Release Notes overview
    pages = crawler.crawl_release_notes(
        start_url="https://confluence-secutix.atlassian.net/wiki/spaces/RN/overview",
        max_pages=500
    )
    
    # Save
    crawler.save_pages(pages)
    
    print("\n" + "="*60)
    print("✅ Ready for vectorization!")
    print("="*60)

if __name__ == "__main__":
    main()
