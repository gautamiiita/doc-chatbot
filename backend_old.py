#!/usr/bin/env python3
"""
FastAPI Backend for Secutix Documentation Chatbot
Handles RAG queries: Retrieve from Pinecone + Generate with Claude
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging
from pinecone import Pinecone
from fastembed import TextEmbedding
import re
from langdetect import detect, LangDetectException
import httpx
import json

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("secutix-docs")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Anthropic SubToken configuration (OAuth via setup-token)
ANTHROPIC_SUBTOKEN = os.getenv("ANTHROPIC_SUBTOKEN")

if not ANTHROPIC_SUBTOKEN:
    logger.warning("⚠️  ANTHROPIC_SUBTOKEN not configured - /query and /summarize will fail")
else:
    logger.info("✅ Using OpenClaw SubToken (from setup-token)")
    logger.info("   This routes through your $20/month Claude subscription")

def call_anthropic_api(model, max_tokens, system_prompt, user_message):
    """
    Call Anthropic API using SubToken with OAuth bearer auth.
    This routes through OpenClaw's setup-token (your Claude subscription).
    Same method as the main OpenClaw session uses.
    """
    try:
        logger.info(f"Calling Anthropic ({model}) via SubToken (OAuth)...")
        
        subtoken = os.getenv("ANTHROPIC_SUBTOKEN")
        if not subtoken:
            raise ValueError("ANTHROPIC_SUBTOKEN not configured in .env")
        
        # Use Bearer auth + oauth-2025-04-20 header (OpenClaw pattern)
        headers = {
            "Authorization": f"Bearer {subtoken}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "oauth-2025-04-20",  # Critical for subscription auth
            "content-type": "application/json",
        }
        
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=body,
            )
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Anthropic API error ({response.status_code}): {error_msg}")
                raise ValueError(f"Anthropic API error: {error_msg}")
            
            data = response.json()
            logger.info("✅ Anthropic API call succeeded (via SubToken)")
            
            # Extract text from response
            if 'content' in data and len(data['content']) > 0:
                return data['content'][0].get('text', '')
            else:
                raise ValueError(f"Unexpected response format: {data}")
            
    except Exception as e:
        logger.error(f"Anthropic API error: {str(e)}", exc_info=True)
        raise

# Language mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'it': 'Italian',
}

# RAG Helper Functions
def select_search_results(search_results, max_docs=3, min_relevance=0.5):
    """
    Select best search results with quality filters.
    
    Args:
        search_results: List of Pinecone matches
        max_docs: Maximum documents to use (default 3)
        min_relevance: Minimum relevance score (0-1, default 0.5 = 50%)
    
    Returns:
        List of selected results with metadata
    """
    selected = []
    
    for match in search_results:
        score = match.get('score', 0)
        
        # Filter by relevance threshold
        if score < min_relevance:
            logger.info(f"Skipping result with score {score} < {min_relevance}")
            continue
        
        if len(selected) >= max_docs:
            break
        
        metadata = match.get('metadata', {})
        selected.append({
            'score': score,
            'title': metadata.get('title', 'Unknown'),
            'text': metadata.get('text', ''),
            'url': metadata.get('url', ''),
            'doc_id': metadata.get('doc_id', 'unknown'),
            'language': metadata.get('language', 'en'),
            'space': metadata.get('space', 'unknown'),
        })
    
    logger.info(f"Selected {len(selected)} documents (max={max_docs}, min_relevance={min_relevance})")
    return selected

def build_rag_prompt(query, search_results, language="en"):
    """
    Build a structured RAG prompt with PM persona.
    
    Returns:
        (system_prompt, user_message) tuple
    """
    
    # Format context from search results
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_parts.append(
            f"Source {i}: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Relevance: {result['score']:.1%}\n\n"
            f"{result['text']}\n"
        )
    
    context = "\n".join(context_parts)
    
    # System prompt with PM persona
    system_prompt = """You are a Senior Product Manager at Secutix, an expert in ticketing and venue management systems.

Your responsibilities:
1. Answer questions about Secutix products, features, and releases with clarity and business context
2. Always cite sources (page titles, links) when providing information
3. Be concise but comprehensive—focus on what users care about: features, benefits, compatibility, release dates
4. When information spans multiple sources, synthesize it clearly and note the version/date context
5. Distinguish between documented facts and any inferences
6. If documentation doesn't cover a question, say so explicitly
7. Use professional language suitable for customers and stakeholders

Remember: You're representing Secutix with authority and transparency."""

    user_message = f"""Based on the following documentation sources, answer this question comprehensively:

QUESTION: {query}

DOCUMENTATION SOURCES:
{context}

Provide a clear, professional answer that:
- Directly addresses the question
- Uses information from the sources above
- Includes source attribution (e.g., "According to [Source Title]...")
- Is suitable for a product stakeholder or customer"""

    return system_prompt, user_message

# Create FastAPI app
app = FastAPI(
    title="Secutix Documentation Chatbot",
    description="RAG-powered Q&A over Release Notes",
    version="1.0.0"
)

# Enable CORS for embedding in websites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint - serve the UI
@app.get("/")
async def root():
    """Serve the chat UI"""
    try:
        with open('public.html', 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Secutix Chatbot</h1><p>Backend is running. Use the API endpoints or serve the UI frontend.</p>")

@app.get("/ui")
async def ui():
    """Serve the chat UI (alternate route)"""
    try:
        with open('public.html', 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"error": "UI not found"}

# Models
class QueryRequest(BaseModel):
    question: str
    language: Optional[str] = "en"
    top_k: Optional[int] = 5

class SearchResult(BaseModel):
    title: str
    text: str
    relevance: float

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    language: str
    detected_language: Optional[str] = None

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "chatbot": "Secutix Documentation Chatbot",
        "pages_indexed": 2487,
        "vector_db": "Pinecone",
        "languages_supported": ["English", "French", "Spanish", "German"],
        "auth_method": "OAuth SubToken (sk-ant-oat-*)",
        "rag_model": "claude-sonnet-4-6",
        "embedding_model": "BAAI/bge-small-en-v1.5",
    }

@app.post("/query")
async def query(request: QueryRequest):
    """
    Query the documentation with RAG and PM persona.
    
    Process:
    1. Detect language of question
    2. Translate to English if needed (for better search)
    3. Search Pinecone (top 10, then filter)
    4. Select best 3 documents with >50% relevance
    5. Generate answer using Claude (PM persona)
    6. Translate answer back if needed
    
    Response includes:
    - Answer (full text)
    - Sources (with relevance scores and direct links)
    - Language detected
    """
    try:
        question = request.question.strip()
        language = request.language or "en"
        
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"=== Query Start: {question[:100]} ===")
        
        # Step 1: Detect language
        detected_lang = "en"
        try:
            detected_lang = detect(question)
        except LangDetectException:
            detected_lang = "en"
        
        logger.info(f"Detected language: {detected_lang}")
        
        # Step 2: Translate question to English if needed
        search_question = question
        if detected_lang != "en":
            logger.info("Translating question to English for search...")
            system = "You are a translator. Translate the user's text to English concisely."
            response = call_anthropic_api(
                model="claude-sonnet-4-6",
                max_tokens=100,
                system_prompt=system,
                user_message=question
            )
            search_question = response.strip()
            logger.info(f"Translated: {search_question}")
        
        # Step 3: Embed and search
        logger.info("Searching Pinecone...")
        embeddings = list(embedding_model.embed([search_question]))
        query_embedding = embeddings[0].tolist()
        
        pinecone_results = index.query(
            vector=query_embedding,
            top_k=10,  # Get top 10, then filter
            include_metadata=True
        )
        
        # Step 4: Select best documents (max 3, >50% relevance)
        selected_docs = select_search_results(
            pinecone_results.get('matches', []),
            max_docs=3,
            min_relevance=0.5
        )
        
        if not selected_docs:
            logger.warning(f"No documents matched threshold (relevance > 0.5)")
            return {
                "question": question,
                "answer": "I found no relevant documentation to answer this question. Please try a different search.",
                "sources": [],
                "language": language,
                "detected_language": detected_lang,
                "message": "No relevant sources found"
            }
        
        logger.info(f"Selected {len(selected_docs)} documents for RAG")
        
        # Step 5: Build prompt and generate answer
        logger.info("Generating answer with PM persona...")
        system_prompt, user_message = build_rag_prompt(search_question, selected_docs, detected_lang)
        
        answer = call_anthropic_api(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system_prompt=system_prompt,
            user_message=user_message
        ).strip()
        
        logger.info(f"Answer generated ({len(answer)} chars)")
        
        # Step 6: Translate answer back if needed
        if detected_lang != "en":
            logger.info(f"Translating answer back to {LANGUAGE_NAMES.get(detected_lang, detected_lang)}...")
            lang_name = LANGUAGE_NAMES.get(detected_lang, detected_lang)
            system = f"You are a translator. Translate the user's text to {lang_name} professionally."
            answer = call_anthropic_api(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system_prompt=system,
                user_message=answer
            ).strip()
        
        # Format response with sources
        sources = [
            {
                "title": doc['title'],
                "url": doc['url'],
                "relevance_score": round(doc['score'] * 100),  # Convert to percentage
                "relevance_percentage": f"{doc['score']:.1%}",
                "snippet": doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
            }
            for doc in selected_docs
        ]
        
        logger.info(f"=== Query Complete ===\n")
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "language": language,
            "detected_language": detected_lang,
            "num_sources": len(sources)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    lang: str = Query("en", description="Language code: en, fr, es, de")
):
    """
    Semantic search with language-aware fallback
    
    Strategy:
    1. Try searching within user's language space first
    2. If <5 results, expand to all languages
    
    Languages: en (English), fr (French), es (Spanish), de (German)
    """
    try:
        embeddings = list(embedding_model.embed([q]))
        query_embedding = embeddings[0].tolist()
        
        # First: Search within user's language
        logger.info(f"Searching for: {q} (language: {lang})")
        
        results = index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True,
            filter={"language": lang}  # Try language-specific search first
        )
        
        sources = []
        for match in results.get('matches', []):
            metadata = match.get('metadata', {})
            page_id = metadata.get('doc_id', 'unknown')
            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'text': metadata.get('text', '')[:300],
                'relevance': round(match.get('score', 0), 3),
                'url': metadata.get('url', f'https://confluence-secutix.atlassian.net/wiki/spaces/RN/pages/{page_id}'),
                'language': metadata.get('language', 'unknown'),
                'space': metadata.get('space', 'unknown')
            })
        
        # If few results in target language, fallback to global search
        if len(sources) < 5:
            logger.info(f"Only {len(sources)} results in {lang}, searching globally...")
            global_results = index.query(vector=query_embedding, top_k=10, include_metadata=True)
            
            # Add global results not already in language-specific results
            existing_ids = {s['title'] for s in sources}
            for match in global_results.get('matches', []):
                if len(sources) >= 10:
                    break
                metadata = match.get('metadata', {})
                title = metadata.get('title', 'Unknown')
                if title not in existing_ids:
                    page_id = metadata.get('doc_id', 'unknown')
                    sources.append({
                        'title': title,
                        'text': metadata.get('text', '')[:300],
                        'relevance': round(match.get('score', 0), 3),
                        'url': metadata.get('url', f'https://confluence-secutix.atlassian.net/wiki/spaces/RN/pages/{page_id}'),
                        'language': metadata.get('language', 'unknown'),
                        'space': metadata.get('space', 'unknown')
                    })
        
        # Sort by relevance and limit to top 5
        sources = sorted(sources, key=lambda x: x['relevance'], reverse=True)[:5]
        
        return {
            'query': q,
            'language_searched': lang,
            'results_count': len(sources),
            'results': sources
        }
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_search(request: QueryRequest):
    """
    Alternative RAG endpoint with different formatting.
    Useful for getting structured, well-formatted answers.
    Also uses document selection (max 3, >50% relevance).
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"=== Summarize Request: {question[:100]} ===")
        
        # Detect language
        detected_lang = "en"
        try:
            detected_lang = detect(question)
        except LangDetectException:
            detected_lang = "en"
        
        # Translate if needed
        search_question = question
        if detected_lang != "en":
            logger.info("Translating question for search...")
            system = "You are a translator. Translate to English concisely."
            search_question = call_anthropic_api(
                model="claude-sonnet-4-6",
                max_tokens=100,
                system_prompt=system,
                user_message=question
            ).strip()
        
        # Search Pinecone
        logger.info("Searching documentation...")
        embeddings = list(embedding_model.embed([search_question]))
        query_embedding = embeddings[0].tolist()
        
        pinecone_results = index.query(vector=query_embedding, top_k=10, include_metadata=True)
        
        # Select best documents (max 3, >50% relevance)
        selected_docs = select_search_results(
            pinecone_results.get('matches', []),
            max_docs=3,
            min_relevance=0.5
        )
        
        if not selected_docs:
            logger.warning("No documents matched threshold")
            return {
                'question': question,
                'answer': "I found no relevant documentation to answer this question.",
                'sources': [],
                'language': request.language or 'en',
                'detected_language': detected_lang,
                'message': 'No relevant sources found'
            }
        
        # Generate formatted answer
        logger.info("Generating formatted answer...")
        system_prompt = """You are a Senior Product Manager at Secutix. Answer questions about our products with clarity and structure.

Format your response with:
- Clear introduction
- Organized sections with headers
- Bullet points for key details
- Always cite sources (e.g., "According to [Title]...")
- Professional, accessible language"""
        
        user_message = f"""Based on this documentation, answer the question comprehensively and well-formatted:

QUESTION: {search_question}

DOCUMENTATION:
"""
        for i, doc in enumerate(selected_docs, 1):
            user_message += f"\n[Source {i}: {doc['title']}]\n{doc['text']}\n"
        
        answer = call_anthropic_api(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system_prompt=system_prompt,
            user_message=user_message
        ).strip()
        
        # Translate back if needed
        if detected_lang != "en":
            lang_name = LANGUAGE_NAMES.get(detected_lang, detected_lang)
            logger.info(f"Translating to {lang_name}...")
            system = f"You are a professional translator. Translate to {lang_name}."
            answer = call_anthropic_api(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system_prompt=system,
                user_message=answer
            ).strip()
        
        # Format sources
        sources = [
            {
                'title': doc['title'],
                'url': doc['url'],
                'relevance_score': round(doc['score'] * 100),
                'relevance_percentage': f"{doc['score']:.1%}",
                'snippet': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
            }
            for doc in selected_docs
        ]
        
        logger.info(f"=== Summarize Complete ===\n")
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'language': request.language or 'en',
            'detected_language': detected_lang,
            'method': 'summarize',
            'num_sources': len(sources)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in summarize: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages")
async def list_pages():
    """List all indexed pages"""
    try:
        import json
        with open('confluence_pages.json') as f:
            pages = json.load(f)
        
        return {
            'total': len(pages),
            'pages': [{'id': p['id'], 'title': p['title']} for p in pages]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
