import os
import aiohttp
import json
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JinaEmbeddingService:
    """Service for generating embeddings using Jina AI API"""
    
    def __init__(self):
        self.api_key = os.environ.get("JINA_API_KEY")
        self.api_url = "https://api.jina.ai/v1/embeddings"
        self.model = "jina-embeddings-v2-base-en"
        
        if not self.api_key:
            logger.warning("JINA_API_KEY not found in environment variables")
            
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if not self.api_key:
            logger.error("Cannot generate embedding: JINA_API_KEY is missing")
            return None
            
        if not text or len(text.strip()) == 0:
            logger.warning("Cannot generate embedding for empty text")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": text,
                "model": self.model
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from Jina API: {response.status} - {error_text}")
                        return None
                        
                    response_data = await response.json()
                    embedding = response_data["data"][0]["embedding"]
                    
                    logger.info(f"Generated embedding with {len(embedding)} dimensions")
                    return embedding
                    
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
            
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts"""
        if not self.api_key:
            logger.error("Cannot generate embeddings: JINA_API_KEY is missing")
            return [None] * len(texts)
            
        embeddings = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Filter out empty texts
            batch = [t for t in batch if t and len(t.strip()) > 0]
            
            if not batch:
                continue
                
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "input": batch,
                    "model": self.model
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, headers=headers, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Error from Jina API: {response.status} - {error_text}")
                            embeddings.extend([None] * len(batch))
                            continue
                            
                        response_data = await response.json()
                        batch_embeddings = [item["embedding"] for item in response_data["data"]]
                        embeddings.extend(batch_embeddings)
                        
                logger.info(f"Generated {len(batch)} embeddings in batch {i//batch_size + 1}")
                
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
                embeddings.extend([None] * len(batch))
                
        return embeddings
        
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
            
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
        
    def find_most_similar(self, query_embedding: List[float], embeddings: List[List[float]], top_k: int = 3) -> List[int]:
        """Find indices of the most similar embeddings to the query embedding"""
        if not query_embedding or not embeddings:
            return []
            
        similarities = []
        for emb in embeddings:
            if emb:
                sim = self.calculate_similarity(query_embedding, emb)
                similarities.append(sim)
            else:
                similarities.append(0.0)
                
        # Get indices of top-k similar embeddings
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return top_indices.tolist()


class MockEmbeddingService:
    """Mock embedding service for testing without API keys"""
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        logger.warning("Using MockEmbeddingService - embeddings will be random and not useful for production")
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a random embedding for testing"""
        # Generate a random unit vector
        embedding = np.random.randn(self.embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
        
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate random embeddings for testing"""
        embeddings = []
        for text in texts:
            if text and len(text.strip()) > 0:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
            else:
                # Add a zero vector for empty text
                embeddings.append([0.0] * self.embedding_dim)
                
        return embeddings
        
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
        
    def find_most_similar(self, query_embedding: List[float], embeddings: List[List[float]], top_k: int = 3) -> List[int]:
        """Find indices of the most similar embeddings to the query embedding"""
        similarities = [self.calculate_similarity(query_embedding, emb) for emb in embeddings]
        
        # Get indices of top-k similar embeddings
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return top_indices.tolist()


def get_embedding_service():
    """Factory function to get the appropriate embedding service"""
    # If JINA_API_KEY is available, use the real service
    if os.environ.get("JINA_API_KEY"):
        return JinaEmbeddingService()
    else:
        # Otherwise use the mock service for testing
        return MockEmbeddingService()
