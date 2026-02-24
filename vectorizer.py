#!/usr/bin/env python3
"""
Document Vectorization Pipeline using FastEmbed (lightweight, open-source)
Chunks documents and sends to Pinecone
"""

import json
import os
from typing import List, Dict
from pinecone import Pinecone
from fastembed import TextEmbedding
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentChunker:
    """Split documents into searchable chunks"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        """
        chunk_size: characters per chunk
        overlap: overlap between consecutive chunks for context
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, text: str, doc_id: str, title: str) -> List[Dict]:
        """Split a document into chunks"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_num = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'id': f"{doc_id}-chunk-{chunk_num}",
                        'title': title,
                        'text': current_chunk.strip(),
                        'chunk_num': chunk_num,
                        'doc_id': doc_id,
                    })
                    chunk_num += 1
                
                # Add overlap from previous chunk
                current_chunk = current_chunk[-self.overlap:] + para + "\n\n"
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'id': f"{doc_id}-chunk-{chunk_num}",
                'title': title,
                'text': current_chunk.strip(),
                'chunk_num': chunk_num,
                'doc_id': doc_id,
            })
        
        return chunks

class PineconeVectorizer:
    """Upload chunks to Pinecone using FastEmbed embeddings"""
    
    def __init__(self, api_key: str, index_name: str, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        model_name: FastEmbed model to use
        - 'BAAI/bge-small-en-v1.5' (384 dims, very fast)
        - 'BAAI/bge-base-en-v1.5' (768 dims, better quality)
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = None
        
        # Load embedding model
        logger.info(f"Loading FastEmbed model: {model_name}...")
        self.model = TextEmbedding(model_name=model_name)
        self.embedding_dim = 384 if "small" in model_name else 768
        logger.info(f"✅ Model loaded. Embedding dimension: {self.embedding_dim}")
        
        self._init_index()
    
    def _init_index(self):
        """Create or get Pinecone index"""
        try:
            # Try to get existing index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"✅ Connected to index: {self.index_name}")
        except Exception as e:
            # Index doesn't exist, create it
            logger.warning(f"⚠️ Index '{self.index_name}' not found, creating...")
            logger.info(f"   Creating index with {self.embedding_dim} dimensions...")
            try:
                from pinecone import ServerlessSpec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                logger.info(f"✅ Index created: {self.index_name}")
                import time
                time.sleep(2)  # Wait for index to be ready
                self.index = self.pc.Index(self.index_name)
            except Exception as e2:
                logger.error(f"Failed to create index: {e2}")
                raise
    
    def vectorize_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """
        Vectorize chunks using FastEmbed and upload to Pinecone
        """
        logger.info(f"Vectorizing {len(chunks)} chunks with FastEmbed...")
        
        # Extract texts for embedding
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = list(self.model.embed(texts, batch_size=32))
        
        # Prepare vectors for Pinecone
        logger.info(f"Uploading to Pinecone in batches of {batch_size}...")
        vectors_to_upload = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector = (
                chunk['id'],
                embedding,
                {
                    'title': chunk['title'],
                    'text': chunk['text'],
                    'doc_id': chunk['doc_id'],
                    'chunk_num': chunk['chunk_num'],
                }
            )
            vectors_to_upload.append(vector)
            
            # Upload in batches
            if len(vectors_to_upload) >= batch_size:
                self.index.upsert(vectors=vectors_to_upload)
                logger.info(f"  ✓ Uploaded {len(vectors_to_upload)} vectors ({i+1}/{len(chunks)})")
                vectors_to_upload = []
        
        # Upload remaining vectors
        if vectors_to_upload:
            self.index.upsert(vectors=vectors_to_upload)
            logger.info(f"  ✓ Uploaded final {len(vectors_to_upload)} vectors")
        
        logger.info(f"✅ All {len(chunks)} chunks vectorized and uploaded to Pinecone!")

def main():
    """Main entry point"""
    
    # Load crawled pages
    if not os.path.exists('confluence_pages.json'):
        logger.error("confluence_pages.json not found. Run crawler first.")
        return
    
    with open('confluence_pages.json') as f:
        pages = json.load(f)
    
    logger.info(f"Loaded {len(pages)} pages")
    
    # Chunk documents
    chunker = DocumentChunker(chunk_size=1000, overlap=100)
    all_chunks = []
    
    for page in pages:
        chunks = chunker.chunk_document(
            text=page['text'],
            doc_id=page['id'],
            title=page['title']
        )
        all_chunks.extend(chunks)
        logger.info(f"  ✓ {page['title'][:40]:40} → {len(chunks)} chunks")
    
    logger.info(f"\n📊 Chunking complete!")
    logger.info(f"   Total chunks: {len(all_chunks)}")
    logger.info(f"   Avg chunk size: {sum(len(c['text']) for c in all_chunks)//len(all_chunks)} chars")
    
    # Save chunks for reference
    with open('chunks.json', 'w') as f:
        json.dump(all_chunks, f, indent=2)
    logger.info(f"   Saved to chunks.json")
    
    # Upload to Pinecone with FastEmbed embeddings
    pinecone_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_key:
        logger.error("❌ PINECONE_API_KEY not found in .env")
        return
    
    logger.info("\n🚀 Starting Pinecone upload with FastEmbed...")
    vectorizer = PineconeVectorizer(pinecone_key, "secutix-docs", model_name="BAAI/bge-small-en-v1.5")
    vectorizer.vectorize_chunks(all_chunks, batch_size=100)
    
    logger.info("\n✅ Pipeline complete! Chatbot is ready to query.")

if __name__ == "__main__":
    main()
