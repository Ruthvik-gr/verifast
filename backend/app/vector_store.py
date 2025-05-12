import os
import json
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """In-memory vector store for storing and retrieving document embeddings"""
    
    def __init__(self, data_dir: str = None):
        """Initialize the vector store"""
        self.documents = []  # List of original documents/chunks
        self.embeddings = []  # List of corresponding embeddings
        self.metadata = []   # List of metadata for each document
        
        # Set data directory for persistence
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
    def add_document(self, document: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Add a document and its embedding to the store"""
        if not document or not embedding:
            logger.warning("Attempted to add empty document or embedding")
            return
            
        self.documents.append(document)
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})
        
        logger.info(f"Added document to vector store. Total documents: {len(self.documents)}")
        
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
            
        for i, (doc, emb, meta) in enumerate(zip(documents, embeddings, metadata_list)):
            if doc and emb:
                self.documents.append(doc)
                self.embeddings.append(emb)
                self.metadata.append(meta)
            else:
                logger.warning(f"Skipping empty document or embedding at index {i}")
                
        logger.info(f"Added {len(documents)} documents to vector store. Total documents: {len(self.documents)}")
        
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, Dict[str, Any], float]]:
        """Search for most similar documents to the query embedding"""
        if not self.embeddings or not query_embedding:
            return []
            
        # Convert query embedding to numpy array
        query_vector = np.array(query_embedding)
        
        # Calculate cosine similarities with all embeddings
        similarities = []
        for emb in self.embeddings:
            # Convert document embedding to numpy array
            doc_vector = np.array(emb)
            
            # Calculate cosine similarity
            sim = np.dot(query_vector, doc_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(doc_vector))
            similarities.append(float(sim))
            
        # Get indices of top-k similar documents
        if not similarities:
            return []
            
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return documents, metadata, and similarities
        results = []
        for idx in top_indices:
            results.append((self.documents[idx], self.metadata[idx], similarities[idx]))
            
        return results
        
    def save(self, filename: str = None):
        """Save the vector store to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vector_store_{timestamp}.json"
            
        filepath = os.path.join(self.data_dir, filename)
        
        # Prepare data for serialization
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "metadata": self.metadata
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved vector store with {len(self.documents)} documents to {filepath}")
        return filepath
        
    def load(self, filename: str) -> bool:
        """Load the vector store from a file"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"Vector store file not found: {filepath}")
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.documents = data.get("documents", [])
            self.embeddings = data.get("embeddings", [])
            self.metadata = data.get("metadata", [])
            
            # Ensure the metadata list is the same length as documents
            if len(self.metadata) < len(self.documents):
                self.metadata.extend([{} for _ in range(len(self.documents) - len(self.metadata))])
                
            logger.info(f"Loaded vector store with {len(self.documents)} documents from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
            
    def clear(self):
        """Clear the vector store"""
        self.documents = []
        self.embeddings = []
        self.metadata = []
        
        logger.info("Cleared vector store")
        
    def get_size(self) -> int:
        """Get the number of documents in the store"""
        return len(self.documents)
        
    def get_document(self, index: int) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get a document and its metadata by index"""
        if 0 <= index < len(self.documents):
            return (self.documents[index], self.metadata[index])
        return None
