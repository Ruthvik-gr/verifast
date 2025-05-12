import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantVectorStore:
    """Qdrant vector store for storing and retrieving document embeddings"""
    
    def __init__(self, collection_name: str = "news_articles", embedding_dim: int = 768):
        """Initialize the Qdrant vector store"""
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        # Get Qdrant configuration from environment variables
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        qdrant_port = int(os.environ.get("QDRANT_PORT", 6333))
        qdrant_mode = os.environ.get("QDRANT_MODE", "memory")  # Default to memory mode
        
        # Connect to Qdrant based on configuration
        if qdrant_mode.lower() == "memory":
            # Use in-memory Qdrant
            self.client = QdrantClient(":memory:")
            logger.info("Using in-memory Qdrant as specified in configuration")
        else:
            # Try to connect to Qdrant server
            try:
                self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
                logger.info(f"Connected to Qdrant server at {qdrant_host}:{qdrant_port}")
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant server at {qdrant_host}:{qdrant_port}: {e}. Falling back to in-memory Qdrant.")
                self.client = QdrantClient(":memory:")
                logger.info("Using in-memory Qdrant as fallback")
            
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()
        
    def _create_collection_if_not_exists(self):
        """Create the collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                )
                logger.info(f"Created collection '{self.collection_name}' in Qdrant")
        except Exception as e:
            logger.warning(f"Error creating collection: {e}. Will retry with operations.")
            # Just continue - we'll create the collection when needed
            
    def add_document(self, document: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Add a document and its embedding to the store"""
        try:
            if metadata is None:
                metadata = {}
                
            # Add timestamp if not provided
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now().isoformat()
                
            # Create a unique ID for the document
            point_id = str(hash(document + metadata.get("url", "") + metadata.get("timestamp", "")))
            
            # Store the document in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "document": document,
                            **metadata
                        }
                    )
                ]
            )
            
            logger.info(f"Added document to Qdrant collection '{self.collection_name}'")
            return point_id
        except Exception as e:
            logger.warning(f"Error adding document to vector store: {e}")
            return None
        
    def add_documents(self, documents: List[str], embeddings: List[List[float]], metadata_list: List[Dict[str, Any]] = None):
        """Add multiple documents and their embeddings to the store"""
        if len(documents) != len(embeddings):
            logger.error(f"Number of documents ({len(documents)}) does not match number of embeddings ({len(embeddings)})")
            return
            
        if metadata_list is None:
            metadata_list = [{} for _ in documents]
        elif len(metadata_list) != len(documents):
            logger.error(f"Number of metadata items ({len(metadata_list)}) does not match number of documents ({len(documents)})")
            return
            
        points = []
        for i, (doc, emb, meta) in enumerate(zip(documents, embeddings, metadata_list)):
            if doc and emb:
                # Prepare metadata
                payload = meta or {}
                payload["document"] = doc
                payload["timestamp"] = datetime.now().isoformat()
                
                # Create point
                points.append(
                    PointStruct(
                        id=self._generate_point_id(),
                        vector=emb,
                        payload=payload
                    )
                )
            else:
                logger.warning(f"Skipping empty document or embedding at index {i}")
                
        if points:
            # Add points to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} documents to Qdrant collection '{self.collection_name}'")
        
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, Dict[str, Any], float]]:
        """Search for most similar documents to the query embedding"""
        if not query_embedding:
            logger.warning("Empty query embedding provided to search")
            return []
            
        # Create a dummy response for when we can't connect to Qdrant
        fallback_response = [
            ("I'm sorry, but I'm currently experiencing issues with my knowledge base. I can still try to help based on my general knowledge.", 
             {"source": "fallback", "timestamp": "2025-05-12T00:00:00"}, 
             1.0)
        ]
            
        try:
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            
            # Format results
            results = []
            for result in search_results:
                document = result.payload.get("document", "")
                # Remove document from metadata to avoid duplication
                metadata = {k: v for k, v in result.payload.items() if k != "document"}
                score = result.score
                results.append((document, metadata, score))
                
            return results if results else fallback_response
            
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {e}")
            # Return a fallback response instead of empty list
            return fallback_response
        
    def clear(self):
        """Clear the vector store by recreating the collection"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}' from Qdrant")
            self._create_collection_if_not_exists()
        except Exception as e:
            logger.error(f"Error clearing Qdrant collection: {e}")
            
    def get_size(self) -> int:
        """Get the number of documents in the store"""
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            return collection_info.vectors_count
        except Exception as e:
            logger.error(f"Error getting collection size: {e}")
            return 0
            
    def _generate_point_id(self) -> str:
        """Generate a unique ID for a point"""
        import uuid
        return str(uuid.uuid4())
