#!/usr/bin/env python3
import os
import requests

confluence_url = "https://confluence-secutix.atlassian.net"
username = "gautam.srivastava@secutix.com"
token = "***REMOVED***"

print("🔍 Testing Confluence API with direct page ID...")

try:
    # Try API v3 directly with the page ID from the URL
    page_id = "43058481"
    response = requests.get(
        f"{confluence_url}/rest/api/3/pages/{page_id}?expand=body.storage,version",
        auth=(username, token),
        timeout=10
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        page = response.json()
        title = page.get("title", "N/A")
        body = page.get("body", {}).get("storage", {}).get("value", "")
        
        print(f"\n✅ Successfully accessed Release Notes!")
        print(f"   Page ID: {page_id}")
        print(f"   Title: {title}")
        print(f"   Content size: {len(body)} bytes (~{len(body)//1024}KB)")
        print(f"   Has content: {'Yes' if len(body) > 100 else 'No'}")
        
        # Check for images
        has_images = '<img' in body or '<ac:image' in body
        print(f"   Has images: {'Yes' if has_images else 'No'}")
        
        # Try to list child pages
        print(f"\n📚 Checking for child pages...")
        child_response = requests.get(
            f"{confluence_url}/rest/api/3/pages/{page_id}/children",
            auth=(username, token),
            timeout=10
        )
        
        if child_response.status_code == 200:
            children = child_response.json()
            results = children.get("results", [])
            print(f"   Found {len(results)} child pages")
            for child in results[:5]:
                print(f"     - {child.get('title')}")
        
    elif response.status_code == 401:
        print("❌ Unauthorized - check credentials")
        print(f"   {response.text[:200]}")
    elif response.status_code == 403:
        print("❌ Forbidden - check permissions")
        print(f"   {response.text[:200]}")
    else:
        print(f"❌ Error {response.status_code}")
        print(f"   {response.text[:300]}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
