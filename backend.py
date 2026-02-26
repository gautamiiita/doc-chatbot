#!/usr/bin/env python3
"""
Secutix Documentation Chatbot - Simplified RAG Backend
Single unified /query endpoint: Search → LLM → Answer + Sources
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging
from pinecone import Pinecone
from fastembed import TextEmbedding
from langdetect import detect, LangDetectException
import httpx

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("secutix-docs")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Anthropic SubToken
ANTHROPIC_SUBTOKEN = os.getenv("ANTHROPIC_SUBTOKEN")
if not ANTHROPIC_SUBTOKEN:
    logger.warning("⚠️  ANTHROPIC_SUBTOKEN not configured")
else:
    logger.info("✅ Using OpenClaw SubToken (from setup-token)")

# Create FastAPI app
app = FastAPI(title="Secutix Documentation Chatbot", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve HTML UI
@app.get("/")
async def root():
    """Serve the chat UI"""
    try:
        with open('public.html', 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Secutix Chatbot</h1><p>Backend running</p>")

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "chatbot": "Secutix Documentation",
        "pages_indexed": 2487,
        "model": "claude-sonnet-4-6",
        "auth": "OpenClaw SubToken"
    }

# Models
class QueryRequest(BaseModel):
    question: str
    language: Optional[str] = "en"

def call_anthropic_api(system_prompt: str, user_message: str) -> str:
    """
    Call Anthropic API with Bearer auth + oauth header
    Uses your Claude subscription (setup-token)
    """
    if not ANTHROPIC_SUBTOKEN:
        raise ValueError("ANTHROPIC_SUBTOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {ANTHROPIC_SUBTOKEN}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "content-type": "application/json",
    }
    
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=body,
            )
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Anthropic error: {error_msg}")
                raise ValueError(f"API error: {error_msg}")
            
            data = response.json()
            return data['content'][0]['text']
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        raise

@app.post("/query")
async def query(request: QueryRequest):
    """
    UNIFIED ENDPOINT: Search → LLM → Answer + Sources
    
    Process:
    1. Detect language of question
    2. Translate to English if needed (for search)
    3. Search Pinecone (get top 10)
    4. Filter: Keep only >50% relevance, max 3 docs
    5. Call LLM with PM persona
    6. Translate answer back to user's language
    7. Return answer + sources with links
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {question[:80]}")
        logger.info(f"{'='*60}\n")
        
        # Step 1: Detect language
        detected_lang = "en"
        try:
            detected_lang = detect(question)
        except:
            detected_lang = "en"
        logger.info(f"1. Detected language: {detected_lang}")
        
        # Step 2: Translate question to English for search
        search_question = question
        if detected_lang != "en":
            logger.info(f"2. Translating question to English...")
            system = "Translate to English. Be concise."
            search_question = call_anthropic_api(system, question).strip()
            logger.info(f"   Translated: {search_question}")
        else:
            logger.info(f"2. Question already in English")
        
        # Step 3: Search Pinecone
        logger.info(f"3. Searching Pinecone (top 10)...")
        embeddings = list(embedding_model.embed([search_question]))
        query_embedding = embeddings[0].tolist()
        
        results = index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True
        )
        logger.info(f"   Found {len(results['matches'])} results")
        
        # Step 4: Filter and select documents
        logger.info(f"4. Filtering documents (>50% relevance, max 3)...")
        selected_docs = []
        for match in results['matches']:
            score = match['score']
            if score < 0.5:  # Below threshold
                continue
            if len(selected_docs) >= 3:  # Max reached
                break
            
            metadata = match['metadata']
            selected_docs.append({
                'score': score,
                'title': metadata.get('title', 'Unknown'),
                'text': metadata.get('text', ''),
                'url': metadata.get('url', ''),
            })
        
        logger.info(f"   Selected {len(selected_docs)} documents")
        
        if not selected_docs:
            logger.warning(f"   No documents met threshold")
            return {
                "question": question,
                "answer": "I couldn't find relevant documentation for your question. Please try rephrasing it.",
                "sources": [],
                "detected_language": detected_lang,
            }
        
        # Step 5: Build context and call LLM
        logger.info(f"5. Calling LLM with PM persona...")
        
        context = ""
        for i, doc in enumerate(selected_docs, 1):
            context += f"\n### Source {i}: {doc['title']}\n"
            context += f"Relevance: {doc['score']:.1%}\n"
            context += f"URL: {doc['url']}\n\n"
            context += f"{doc['text']}\n"
        
        system_prompt = """You are a Senior Product Manager at Secutix, an expert in ticketing and venue management systems.

Answer the user's question based on the provided documentation sources.
- Be clear, concise, and authoritative
- Always cite sources (e.g., "According to [Source Title]...")
- Include relevant details from the documentation
- If information isn't in the docs, say so explicitly"""
        
        user_message = f"""Based on these documentation sources, answer the question:

QUESTION: {search_question}

DOCUMENTATION SOURCES:
{context}

Provide a clear, professional answer suitable for a product stakeholder or customer."""
        
        answer = call_anthropic_api(system_prompt, user_message).strip()
        logger.info(f"   Answer generated ({len(answer)} chars)")
        
        # Step 6: Translate answer back if needed
        if detected_lang != "en":
            logger.info(f"6. Translating answer back to {detected_lang}...")
            system = f"Translate to {detected_lang}. Keep professional tone."
            answer = call_anthropic_api(system, answer).strip()
        else:
            logger.info(f"6. Answer in English, no translation needed")
        
        # Step 7: Format sources for response
        sources = []
        for doc in selected_docs:
            sources.append({
                "title": doc['title'],
                "url": doc['url'],
                "relevance_percentage": f"{doc['score']:.1%}",
                "relevance_score": round(doc['score'] * 100),
            })
        
        logger.info(f"\n✅ COMPLETE\n{'='*60}\n")
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "detected_language": detected_lang,
            "num_sources": len(sources),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    """
    Quick semantic search (without LLM)
    """
    try:
        embeddings = list(embedding_model.embed([q]))
        query_embedding = embeddings[0].tolist()
        
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        
        sources = []
        for match in results['matches']:
            metadata = match['metadata']
            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'url': metadata.get('url', ''),
                'relevance': match['score'],
                'text': metadata.get('text', '')[:200],
            })
        
        return {
            'query': q,
            'results_count': len(sources),
            'results': sources
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
