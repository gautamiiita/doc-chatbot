#!/usr/bin/env python3
"""
Build script: Orchestrates the full pipeline
1. Crawl Confluence pages
2. Chunk documents
3. Vectorize with sentence-transformers
4. Upload to Pinecone
"""

import subprocess
import sys
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(script, name):
    """Run a Python script and handle errors"""
    logger.info(f"\n{'='*60}")
    logger.info(f"📍 Running: {name}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script], check=True)
        logger.info(f"✅ {name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {name} failed with exit code {e.returncode}")
        return False

def check_env():
    """Verify .env has required keys"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ["PINECONE_API_KEY", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    
    if missing:
        logger.error(f"❌ Missing .env variables: {', '.join(missing)}")
        return False
    
    logger.info("✅ All .env variables present")
    return True

def check_confluence_pages():
    """Check if pages have been crawled"""
    if not os.path.exists('confluence_pages.json'):
        logger.warning("⚠️ confluence_pages.json not found")
        logger.info("   Skipping vectorization (crawl first with: python confluence_crawler.py)")
        return False
    
    with open('confluence_pages.json') as f:
        pages = json.load(f)
    
    logger.info(f"✅ Found {len(pages)} crawled pages")
    return True

def main():
    logger.info("🚀 Documentation Chatbot Build Pipeline")
    
    # Check environment
    if not check_env():
        sys.exit(1)
    
    # Check if we have pages to vectorize
    if not check_confluence_pages():
        logger.info("\n📋 Next step: Run the crawler")
        logger.info("   python confluence_crawler.py")
        sys.exit(0)
    
    # Run vectorization
    if not run_command('vectorizer.py', 'Vectorization Pipeline'):
        logger.error("Build failed during vectorization")
        sys.exit(1)
    
    # Success
    logger.info(f"\n{'='*60}")
    logger.info("✅ BUILD COMPLETE!")
    logger.info(f"{'='*60}")
    logger.info("\n📊 Next steps:")
    logger.info("   1. Run backend: uvicorn backend:app --reload")
    logger.info("   2. Test queries at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
