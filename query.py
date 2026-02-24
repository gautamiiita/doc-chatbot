#!/usr/bin/env python3
"""
Query script: Search Pinecone + generate answer with Claude
"""

import os
import sys
from pinecone import Pinecone
from fastembed import TextEmbedding
from anthropic import Anthropic
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class DocumentChatbot:
    def __init__(self):
        # Initialize Pinecone
        pinecone_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=pinecone_key)
        self.index = self.pc.Index("secutix-docs")
        logger.info("✅ Connected to Pinecone index: secutix-docs")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("✅ Embedding model loaded")
        
        # Initialize Claude
        self.client = Anthropic()
        logger.info("✅ Claude API ready")
    
    def search_documents(self, query: str, top_k: int = 5) -> list:
        """Search Pinecone for relevant documents"""
        # Embed the query
        embeddings = list(self.embedding_model.embed([query]))
        query_embedding = embeddings[0].tolist() if hasattr(embeddings[0], 'tolist') else list(embeddings[0])
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results.get('matches', [])
    
    def generate_answer(self, query: str, search_results: list) -> str:
        """Generate answer using Claude"""
        
        # Build context from search results
        context = "# Relevant Documentation\n\n"
        for i, match in enumerate(search_results, 1):
            metadata = match.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            text = metadata.get('text', '')
            context += f"## Source {i}: {title}\n{text}\n\n"
        
        # Build prompt for Claude
        prompt = f"""{self.client.HUMAN_PROMPT} You are a helpful assistant answering questions about Secutix documentation.

Based on the following documentation excerpts, answer the user's question. Be concise and specific.
If the answer is not in the documentation, say so.

{context}

User Question: {query}{self.client.AI_PROMPT}"""
        
        # Call Claude with completions API
        response = self.client.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=1024,
            prompt=prompt
        )
        
        return response.completion
    
    def chat(self, query: str):
        """Full query pipeline"""
        logger.info(f"\n🔍 Searching for: {query}")
        
        # Search
        results = self.search_documents(query, top_k=5)
        
        if not results:
            logger.info("❌ No relevant documents found")
            return
        
        logger.info(f"✅ Found {len(results)} relevant chunks (max score: {results[0]['score']:.3f})")
        logger.info(f"\n💬 Generating answer with Claude...\n")
        
        # Generate answer
        answer = self.generate_answer(query, results)
        
        logger.info(f"Answer:\n{answer}")
        
        # Show sources
        logger.info(f"\n📚 Sources:")
        for i, match in enumerate(results[:3], 1):
            title = match.get('metadata', {}).get('title', 'Unknown')
            score = match.get('score', 0)
            logger.info(f"   {i}. {title} (relevance: {score:.3f})")

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python3 query.py \"<your question>\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    chatbot = DocumentChatbot()
    chatbot.chat(query)

if __name__ == "__main__":
    main()
