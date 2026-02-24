#!/usr/bin/env python3
"""Test Confluence API access."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

confluence_url = os.getenv("CONFLUENCE_URL")
username = os.getenv("CONFLUENCE_USERNAME")
token = os.getenv("CONFLUENCE_API_TOKEN")

print("🔍 Testing Confluence API Connection...")
print(f"   URL: {confluence_url}")
print(f"   User: {username}")

try:
    # Test 1: Get Release Notes space info
    response = requests.get(
        f"{confluence_url}/rest/api/2/space/RN",
        auth=(username, token),
        timeout=10
    )
    
    if response.status_code == 200:
        space_data = response.json()
        print(f"\n✅ Connected to Confluence!")
        print(f"   Space: {space_data.get('name')}")
        print(f"   Key: {space_data.get('key')}")
    else:
        print(f"\n❌ Failed: HTTP {response.status_code}")
        print(f"   {response.text[:200]}")
        exit(1)
    
    # Test 2: Count pages in Release Notes
    response = requests.get(
        f"{confluence_url}/rest/api/2/search?cql=space=RN&limit=1",
        auth=(username, token),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("totalSize", 0)
        print(f"\n📄 Release Notes Space:")
        print(f"   Total pages: {total}")
        
        # Show first few pages
        if data.get("results"):
            print(f"   Sample pages:")
            for page in data["results"][:3]:
                print(f"     - {page.get('title')}")
    else:
        print(f"❌ Search failed: {response.status_code}")
        exit(1)
    
    # Test 3: Get the main Release Notes page
    response = requests.get(
        f"{confluence_url}/rest/api/3/pages/43058481?expand=body.storage,version",
        auth=(username, token),
        timeout=10
    )
    
    if response.status_code == 200:
        page = response.json()
        title = page.get("title")
        version = page.get("version", {}).get("number")
        body = page.get("body", {}).get("storage", {}).get("value", "")
        body_length = len(body)
        
        print(f"\n📋 Main Release Notes Page:")
        print(f"   Title: {title}")
        print(f"   Version: {version}")
        print(f"   Content size: {body_length} bytes (~{body_length // 1024}KB)")
        print(f"   Has content: {'Yes' if body_length > 100 else 'No'}")
        
        # Check for images
        has_images = '<img' in body or '<ac:image' in body
        print(f"   Has images: {'Yes' if has_images else 'No'}")
        
    else:
        print(f"⚠️  Could not fetch main page: {response.status_code}")
    
    print("\n" + "="*50)
    print("✅ Confluence API is working!")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
