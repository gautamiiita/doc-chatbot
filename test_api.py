#!/usr/bin/env python3
"""Test Confluence and Pinecone API connections."""

import os
import sys
from dotenv import load_dotenv
import requests
from pinecone import Pinecone

load_dotenv()

def test_confluence():
    """Test Confluence API access."""
    print("🔍 Testing Confluence API...")
    
    confluence_url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")
    
    if not all([confluence_url, username, token]):
        print("❌ Missing Confluence credentials in .env")
        return False
    
    try:
        # Test basic API access - list pages in Release Notes space
        response = requests.get(
            f"{confluence_url}/rest/api/2/search?cql=space=RN&limit=1",
            auth=(username, token),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total_pages = data.get("totalSize", 0)
            print(f"✅ Confluence connected!")
            print(f"   Found {total_pages} pages in Release Notes space")
            return True
        else:
            print(f"❌ Confluence API returned {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Confluence connection failed: {str(e)}")
        return False

def test_pinecone():
    """Test Pinecone API access."""
    print("\n🔍 Testing Pinecone API...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not api_key:
        print("❌ Missing Pinecone API key in .env")
        return False
    
    try:
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"✅ Pinecone connected!")
        print(f"   Available indexes: {indexes.names if hasattr(indexes, 'names') else 'None yet'}")
        
        # Check if our index exists
        if index_name in (indexes.names if hasattr(indexes, 'names') else []):
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"   Index '{index_name}' exists with {stats.total_vector_count} vectors")
        else:
            print(f"   Index '{index_name}' does not exist yet (will create during vectorization)")
        
        return True
        
    except Exception as e:
        print(f"❌ Pinecone connection failed: {str(e)}")
        return False

def test_claude():
    """Test Claude API access."""
    print("\n🔍 Testing Claude API...")
    
    api_key = os.getenv("CLAUDE_API_KEY")
    
    if not api_key or api_key == "your_claude_api_key_here":
        print("⚠️  Claude API key not set (optional for now)")
        print("   You can set it later: export CLAUDE_API_KEY=sk-ant-...")
        return True
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        print(f"✅ Claude API connected!")
        return True
        
    except Exception as e:
        print(f"❌ Claude API failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Documentation Chatbot - API Test")
    print("=" * 50)
    
    results = {
        "Confluence": test_confluence(),
        "Pinecone": test_pinecone(),
        "Claude": test_claude(),
    }
    
    print("\n" + "=" * 50)
    print("Summary:")
    for service, success in results.items():
        status = "✅ Ready" if success else "❌ Failed"
        print(f"  {service}: {status}")
    print("=" * 50)
    
    sys.exit(0 if all(results.values()) else 1)
