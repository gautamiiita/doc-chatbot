#!/usr/bin/env python3
"""
Recursive Confluence Crawler
Traverses the page hierarchy to fetch ALL pages
"""

import requests
import json
import re
from html.parser import HTMLParser
from typing import List, Dict, Set
from datetime import datetime
import logging
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML while preserving structure"""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_code = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'code' or tag == 'pre':
            self.in_code = True
            self.text.append("\n```\n")
        elif tag in ['p', 'div', 'li']:
            self.text.append("\n")
        elif tag in ['h1', 'h2', 'h3', 'h4']:
            self.text.append("\n## ")
        elif tag == 'br':
            self.text.append("\n")
            
    def handle_endtag(self, tag):
        if tag == 'code' or tag == 'pre':
            self.in_code = False
            self.text.append("\n```\n")
        
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)
            
    def get_text(self) -> str:
        return " ".join(self.text)

class RecursiveConfluenceCrawler:
    """Recursively crawl Confluence hierarchy"""
    
    def __init__(self, base_url: str, username: str, token: str):
        self.base_url = base_url
        self.auth = (username, token)
        self.pages = []
        self.seen_ids: Set[str] = set()
        self.pages_fetched = 0
        self.pages_failed = 0
        
    def extract_text(self, html_content: str) -> str:
        """Extract clean text from HTML"""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            text = extractor.get_text()
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"Error extracting text: {str(e)}")
            return ""
    
    def fetch_page(self, page_id: str) -> Dict:
        """Fetch a single page"""
        try:
            url = f"{self.base_url}/{page_id}"
            params = {'expand': 'body.storage,version,space,child.page'}
            
            response = requests.get(url, params=params, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch page {page_id}: HTTP {response.status_code}")
                self.pages_failed += 1
                return None
                
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            self.pages_failed += 1
            return None
    
    def crawl_page_recursive(self, page_id: str, space_key: str = "RN", depth: int = 0):
        """Recursively crawl a page and its children"""
        
        # Skip if already seen
        if page_id in self.seen_ids:
            return
        
        self.seen_ids.add(page_id)
        indent = "  " * depth
        
        # Fetch page
        page_data = self.fetch_page(page_id)
        if not page_data:
            return
        
        # Extract page info
        body = page_data.get('body', {}).get('storage', {}).get('value', '')
        text = self.extract_text(body)
        
        page_info = {
            'id': page_id,
            'title': page_data.get('title', ''),
            'url': f"https://confluence-secutix.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}",
            'status': page_data.get('status', 'CURRENT'),
            'version': page_data.get('version', {}).get('number', 0),
            'text': text,
            'content_size': len(body),
            'text_size': len(text),
        }
        
        self.pages.append(page_info)
        self.pages_fetched += 1
        
        logger.info(f"{indent}✓ {page_info['title'][:60]} ({len(text)} chars)")
        
        # Fetch children
        children = page_data.get('child', {}).get('page', {})
        child_results = children.get('results', [])
        
        if child_results:
            logger.info(f"{indent}  → {len(child_results)} child pages")
            for child in child_results:
                child_id = child.get('id')
                self.crawl_page_recursive(child_id, space_key, depth + 1)
        
        # Show progress
        if self.pages_fetched % 10 == 0:
            logger.info(f"Progress: {self.pages_fetched} pages fetched...")
    
    def crawl_space(self, space_key: str = "RN", root_page_id: str = "43058481"):
        """Start recursive crawl from root page"""
        logger.info(f"Starting recursive crawl of space {space_key} from page {root_page_id}...")
        
        self.crawl_page_recursive(root_page_id, space_key)
        
        logger.info(f"\n✅ Crawl complete: {self.pages_fetched} pages fetched, {self.pages_failed} failed")
        return self.pages
    
    def save_pages(self, pages: List[Dict], filename: str = "confluence_pages.json"):
        """Save crawled pages to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(pages)} pages to {filename}")
            
            # Statistics
            total_chars = sum(p['text_size'] for p in pages)
            logger.info(f"\n📊 Statistics:")
            logger.info(f"   Total pages: {len(pages)}")
            logger.info(f"   Total content: {total_chars:,} characters (~{total_chars//1024}KB)")
            logger.info(f"   Avg page size: {total_chars//len(pages) if pages else 0:,} chars")
            
        except Exception as e:
            logger.error(f"Error saving pages: {str(e)}")

def main():
    """Main entry point"""
    
    base_url = "https://confluence-secutix.atlassian.net/wiki/rest/api/content"
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")
    
    if not username or not token:
        logger.error("Missing CONFLUENCE_USERNAME or CONFLUENCE_API_TOKEN in .env")
        return
    
    # Create crawler
    crawler = RecursiveConfluenceCrawler(base_url, username, token)
    
    # Crawl Release Notes space recursively from root page
    pages = crawler.crawl_space(space_key="RN", root_page_id="43058481")
    
    # Save to file
    crawler.save_pages(pages)
    
    print("\n" + "="*60)
    print("✅ Ready for vectorization!")
    print("="*60)

if __name__ == "__main__":
    main()
