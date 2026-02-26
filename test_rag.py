#!/usr/bin/env python3
"""
Quick test script for RAG endpoints
Tests the new document selection and PM persona implementation
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing /health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_search():
    """Test search endpoint"""
    print("\n=== Testing /search ===")
    params = {
        "q": "What are the new features in S-360 v4?",
        "lang": "en"
    }
    response = requests.get(f"{BASE_URL}/search", params=params)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Query: {data['query']}")
    print(f"Results: {data['results_count']}")
    for i, result in enumerate(data['results'], 1):
        print(f"\n  {i}. {result['title']}")
        print(f"     Relevance: {result['relevance']:.1%}")
        print(f"     URL: {result['url']}")
        print(f"     Snippet: {result['text'][:100]}...")

def test_query():
    """Test query endpoint with RAG and PM persona"""
    print("\n=== Testing /query (Full RAG) ===")
    payload = {
        "question": "What are the main features of S-360 v4?",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/query", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuestion: {data['question']}")
        print(f"Detected Language: {data['detected_language']}")
        print(f"Sources Used: {data['num_sources']}/3 max")
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nSources:")
        for i, source in enumerate(data['sources'], 1):
            print(f"\n  {i}. {source['title']}")
            print(f"     Relevance: {source['relevance_percentage']}")
            print(f"     URL: {source['url']}")
            print(f"     Snippet: {source['snippet']}")
    else:
        print(f"Error: {response.text}")

def test_query_multilingual():
    """Test query in a different language"""
    print("\n=== Testing /query (Multilingual - French) ===")
    payload = {
        "question": "Quelles sont les nouvelles fonctionnalités de S-360 v4?",
        "language": "fr"
    }
    response = requests.post(f"{BASE_URL}/query", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuestion (French): {data['question']}")
        print(f"Detected Language: {data['detected_language']}")
        print(f"Answer Preview: {data['answer'][:200]}...")
    else:
        print(f"Error: {response.text}")

def test_summarize():
    """Test summarize endpoint"""
    print("\n=== Testing /summarize (Structured Format) ===")
    payload = {
        "question": "Tell me about release notes for the latest S-360 version",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/summarize", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuestion: {data['question']}")
        print(f"Sources Used: {data['num_sources']}/3 max")
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nSources:")
        for i, source in enumerate(data['sources'], 1):
            print(f"\n  {i}. {source['title']}")
            print(f"     Relevance: {source['relevance_percentage']}")
            print(f"     URL: {source['url']}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("🤖 Secutix RAG Chatbot - Test Suite")
    print("=" * 50)
    
    try:
        # Test in order
        test_health()
        test_search()
        test_query()
        test_query_multilingual()
        test_summarize()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to {BASE_URL}")
        print("Make sure the backend is running: python backend.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
