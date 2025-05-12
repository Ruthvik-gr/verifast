import os
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

from .news_ingestion import NewsIngestionService
from .embedding_service import get_embedding_service
from .qdrant_store import QdrantVectorStore
from .groq_service import get_groq_service
from .models import ChatMessage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RagPipeline:
    """Retrieval-Augmented Generation pipeline for news articles"""
    
    def __init__(self):
        self.news_service = NewsIngestionService()
        self.embedding_service = get_embedding_service()
        try:
            self.vector_store = QdrantVectorStore(collection_name="news_articles")
            logger.info("Successfully created QdrantVectorStore")
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            # Create a dummy vector store that won't crash the application
            self.vector_store = None
        self.groq_service = get_groq_service()
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the RAG pipeline"""
        if self.is_initialized:
            logger.info("RAG pipeline already initialized")
            return
        
        logger.info("Initializing RAG pipeline")
        try:
            # Check if vector store is available
            if self.vector_store is None:
                logger.warning("Vector store is not available, skipping initialization")
                self.is_initialized = True  # Mark as initialized to avoid repeated attempts
                return
                
            # Step 1: Fetch and process news articles
            articles = await self.news_service.fetch_articles_with_content(limit=50)
            
            if not articles:
                logger.warning("No articles fetched during initialization")
                self.is_initialized = True  # Mark as initialized anyway
                return
                
            logger.info(f"Fetched {len(articles)} articles for processing")
            
            # Step 2: Process articles and create chunks
            all_chunks = []
            all_metadata = []
            
            for article in articles:
                # Split article into chunks of approximately 200 words
                chunks = self._split_text(article["content"])
                
                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "title": article["title"],
                        "url": article["url"],
                        "published_date": article["published_date"]
                    })
            
            logger.info(f"Created {len(all_chunks)} chunks from articles")
            
            # Step 3: Generate embeddings for chunks
            embeddings = await self.embedding_service.generate_embeddings_batch(all_chunks)
            
            # Step 4: Add chunks and embeddings to vector store
            valid_chunks = []
            valid_embeddings = []
            valid_metadata = []
            
            for i, (chunk, embedding, metadata) in enumerate(zip(all_chunks, embeddings, all_metadata)):
                if embedding is not None:
                    valid_chunks.append(chunk)
                    valid_embeddings.append(embedding)
                    valid_metadata.append(metadata)
            
            self.vector_store.add_documents(valid_chunks, valid_embeddings, valid_metadata)
            
            logger.info(f"Added {self.vector_store.get_size()} chunks to vector store")
            
            self.is_initialized = True
            logger.info("RAG pipeline initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing RAG pipeline: {e}")
            # Try to load from saved vector store if available
            self._try_load_saved_vectors()
    
    def _try_load_saved_vectors(self):
        """Check if Qdrant already has data"""
        # If vector store is not available, return False
        if self.vector_store is None:
            logger.warning("Vector store is not available, cannot load saved vectors")
            return False
            
        try:
            size = self.vector_store.get_size()
            if size > 0:
                self.is_initialized = True
                logger.info(f"Found existing data in Qdrant with {size} documents")
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking Qdrant data: {e}")
            return False
    
    def _split_text(self, text: str, chunk_size: int = 200) -> List[str]:
        """Split text into chunks of approximately chunk_size words"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    async def generate_response(self, query: str, history: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate response for a query using the RAG pipeline"""
        # Ensure the pipeline is initialized
        if not self.is_initialized:
            try:
                await self.initialize()
                if not self.is_initialized:
                    yield "I'm having trouble accessing news information right now. Please try again later."
                    return
            except Exception as e:
                logger.error(f"Error initializing RAG pipeline on demand: {e}")
                yield "I'm having trouble accessing news information right now. Please try again later."
                return
                
        try:
            # Step 1: Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            if not query_embedding:
                yield "I'm having trouble processing your query. Please try again later."
                return
                
            # Step 2: Search for relevant chunks in the vector store
            if self.vector_store is None:
                search_results = []
                logger.warning("Vector store is not available, skipping search")
            else:
                search_results = self.vector_store.search(query_embedding, top_k=3)
            
            # Check if we got a fallback response
            is_fallback = any(metadata.get('source') == 'fallback' for _, metadata, _ in search_results)
            
            if not search_results or (is_fallback and 'news' in query.lower()):
                yield "I'm having trouble accessing my news database right now. I can still try to help with general questions, but I might not have the latest news information."
                return
                
            # Step 3: Prepare context from relevant chunks
            contexts = []
            for document, metadata, score in search_results:
                source_info = f"From: {metadata.get('title', 'Unknown Article')}"
                contexts.append(f"{document}\n{source_info}")
                
            combined_context = "\n\n---\n\n".join(contexts)
            
            # Step 4: Generate response using Groq
            async for token in self.groq_service.generate_streaming_response(query, combined_context, history):
                yield token
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"I'm sorry, but I encountered an error while trying to answer your question: {str(e)}"
    
    async def refresh_articles(self):
        """Refresh the articles and update the vector store"""
        logger.info("Refreshing news articles")
        
        try:
            # Save the current vector store size for comparison
            original_size = self.vector_store.get_size()
            
            # Fetch new articles
            articles = await self.news_service.fetch_articles_with_content(limit=20)
            
            if not articles:
                logger.warning("No new articles fetched during refresh")
                return False
                
            # Process articles and create chunks
            all_chunks = []
            all_metadata = []
            
            for article in articles:
                chunks = self._split_text(article["content"])
                
                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "title": article["title"],
                        "url": article["url"],
                        "published_date": article["published_date"]
                    })
            
            # Generate embeddings for chunks
            embeddings = await self.embedding_service.generate_embeddings_batch(all_chunks)
            
            # Add chunks and embeddings to vector store
            valid_chunks = []
            valid_embeddings = []
            valid_metadata = []
            
            for i, (chunk, embedding, metadata) in enumerate(zip(all_chunks, embeddings, all_metadata)):
                if embedding is not None:
                    valid_chunks.append(chunk)
                    valid_embeddings.append(embedding)
                    valid_metadata.append(metadata)
            
            self.vector_store.add_documents(valid_chunks, valid_embeddings, valid_metadata)
            
            new_size = self.vector_store.get_size()
            logger.info(f"Added {new_size - original_size} new chunks to vector store")
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing articles: {e}")
            return False
