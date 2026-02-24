#!/usr/bin/env python3
"""
Confluence Document Crawler
Fetches all pages from Release Notes and prepares for vectorization
"""

import requests
import json
import re
from html.parser import HTMLParser
from typing import List, Dict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML while preserving structure"""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_code = False
        self.in_link = False
        self.current_link = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == 'code' or tag == 'pre':
            self.in_code = True
            self.text.append("\n```\n")
        elif tag == 'a':
            attrs_dict = dict(attrs)
            self.current_link = attrs_dict.get('href', '')
            self.in_link = True
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
        elif tag == 'a':
            if self.current_link:
                self.text.append(f" ({self.current_link})")
            self.in_link = False
            
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)
            
    def get_text(self) -> str:
        return " ".join(self.text)

class ConfluenceCrawler:
    """Crawl Confluence Release Notes documentation"""
    
    def __init__(self, base_url: str, username: str, token: str):
        self.base_url = base_url
        self.auth = (username, token)
        self.pages_fetched = 0
        self.pages_failed = 0
        
    def fetch_page(self, page_id: str) -> Dict:
        """Fetch a single page with all expansions"""
        try:
            url = f"{self.base_url}/{page_id}"
            params = {
                'expand': 'body.storage,version,space,ancestors'
            }
            
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
    
    def extract_text(self, html_content: str) -> str:
        """Extract clean text from HTML storage format"""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            text = extractor.get_text()
            
            # Clean up multiple spaces and newlines
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            return text.strip()
        except Exception as e:
            logger.warning(f"Error extracting text: {str(e)}")
            return ""
    
    def crawl_space(self, space_key: str = "RN", limit: int = 1000) -> List[Dict]:
        """Crawl pages in a space using search API (respects limit)"""
        logger.info(f"Starting crawl of space {space_key} (limit: {limit} pages)...")
        
        pages = []
        seen_page_ids = set()  # Track seen pages to avoid duplicates
        start = 0
        
        while self.pages_fetched < limit:
            try:
                # Use search API with CQL to find pages
                search_url = f"{self.base_url.replace('/content', '')}/search"
                batch_size = min(50, limit - self.pages_fetched)
                
                params = {
                    'cql': f'space={space_key} AND type=page',
                    'limit': batch_size,
                    'start': start,
                    'expand': 'content.body.storage,content.version'
                }
                
                response = requests.get(search_url, params=params, auth=self.auth, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Failed to search pages: HTTP {response.status_code}")
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info("No more pages found")
                    break
                
                logger.info(f"Batch {start//batch_size + 1}: {len(results)} pages (start={start}, total fetched={self.pages_fetched}/{limit})...")
                
                batch_had_new = False
                for result in results:
                    # Stop if we've reached the limit
                    if self.pages_fetched >= limit:
                        logger.info(f"Reached limit of {limit} pages")
                        break
                    
                    # Search results have 'content' key with page details
                    page_data = result.get('content', {})
                    page_id = page_data.get('id')
                    
                    # Skip if we've already seen this page
                    if page_id in seen_page_ids:
                        continue
                    
                    seen_page_ids.add(page_id)
                    batch_had_new = True
                    
                    # Fetch full page details to get body
                    full_page = self.fetch_page(page_id)
                    if not full_page:
                        continue
                    
                    body = full_page.get('body', {}).get('storage', {}).get('value', '')
                    text = self.extract_text(body)
                    
                    page_info = {
                        'id': page_id,
                        'title': full_page.get('title', ''),
                        'url': f"https://confluence-secutix.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}",
                        'status': full_page.get('status', 'CURRENT'),
                        'version': full_page.get('version', {}).get('number', 0),
                        'created': full_page.get('metadata', {}).get('created', ''),
                        'updated': full_page.get('version', {}).get('when', ''),
                        'text': text,
                        'content_size': len(body),
                        'text_size': len(text),
                    }
                    
                    pages.append(page_info)
                    self.pages_fetched += 1
                    if self.pages_fetched % 10 == 0:
                        logger.info(f"  ✓ Fetched {self.pages_fetched} pages so far...")
                
                # If no new pages in this batch, we've hit the end
                if not batch_had_new:
                    logger.info("No new pages in this batch - pagination complete")
                    break
                
                # Move to next batch
                start += batch_size
                
            except Exception as e:
                logger.error(f"Error during crawl: {str(e)}")
                break
        
        logger.info(f"\n✅ Crawl complete: {self.pages_fetched} pages fetched, {self.pages_failed} failed")
        return pages
    
    def save_pages(self, pages: List[Dict], filename: str = "confluence_pages.json"):
        """Save crawled pages to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(pages)} pages to {filename}")
            
            # Print statistics
            total_chars = sum(p['text_size'] for p in pages)
            logger.info(f"\n📊 Statistics:")
            logger.info(f"   Total pages: {len(pages)}")
            logger.info(f"   Total content: {total_chars:,} characters (~{total_chars//1024}KB)")
            logger.info(f"   Avg page size: {total_chars//len(pages) if pages else 0:,} chars")
            
        except Exception as e:
            logger.error(f"Error saving pages: {str(e)}")

def main():
    """Main entry point"""
    
    # Configuration
    base_url = "https://confluence-secutix.atlassian.net/wiki/rest/api/content"
    username = "gautam.srivastava@secutix.com"
    token = "ATATT3xFfGF0j2StmTxFMgIt5_jF11-UAKtxZl895-SG4hLpD0s_082YM4AeX9ZPLFzOm3LT1bQGhemLNgsnOMzNs33H38hpJfkX5Ll4ieYn-zI-0PWcEiSEj_qaFbJlHuITv2JeItGIw2SafrR6LVg8OPgwlvlBWBibljYQKNDmjEFxBXKoirk=AD0E5D08"
    
    # Create crawler
    crawler = ConfluenceCrawler(base_url, username, token)
    
    # Crawl Release Notes space (get all pages)
    pages = crawler.crawl_space(space_key="RN", limit=1000)
    
    # Save to file
    crawler.save_pages(pages)
    
    print("\n" + "="*60)
    print("✅ Ready for vectorization!")
    print("="*60)

if __name__ == "__main__":
    main()
