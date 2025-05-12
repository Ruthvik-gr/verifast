import redis
import json
import logging
import uuid
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from .models import ChatMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Manages chat history storage with Redis and in-memory fallback"""
    
    def __init__(self):
        # Get Redis configuration from environment variables
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        """Initialize the chat history manager"""
        # Set up Redis connection - will connect to localhost by default
        self.redis_available = False
        try:
            self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True, socket_timeout=2)
            # Test connection
            self.redis.ping()
            self.redis_available = True
            logger.info("Connected to Redis successfully")
        except (redis.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.warning(f"Could not connect to Redis: {e}. Using in-memory fallback.")
            self.redis = None
            self.fallback_storage = {}
            
        # Set TTL for chat histories (24 hours)
        self.ttl = 24 * 60 * 60
        
    def _get_key(self, session_id: str) -> str:
        """Generate Redis key for a session"""
        return f"chat:history:{session_id}"
        
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        if self.redis_available:
            try:
                return bool(self.redis.exists(self._get_key(session_id)))
            except Exception as e:
                logger.error(f"Error checking session existence in Redis: {e}")
                self.redis_available = False
                # Fall back to in-memory if Redis fails
                return session_id in self.fallback_storage
        else:
            return session_id in self.fallback_storage
            
    def create_session(self, session_id: str) -> bool:
        """Create a new chat session"""
        if self.session_exists(session_id):
            logger.debug(f"Session already exists: {session_id}")
            return False
            
        try:
            if self.redis_available:
                # Store empty list as JSON string
                self.redis.set(self._get_key(session_id), json.dumps([]))
                self.redis.expire(self._get_key(session_id), self.ttl)
                logger.info(f"Created new session in Redis: {session_id}")
            else:
                self.fallback_storage[session_id] = []
                logger.info(f"Created new session in memory: {session_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            # If Redis fails, fall back to in-memory
            if not hasattr(self, 'fallback_storage'):
                self.fallback_storage = {}
            self.fallback_storage[session_id] = []
            self.redis_available = False
            return True
        
    def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to the chat history"""
        if not self.session_exists(session_id):
            self.create_session(session_id)
            
        # Ensure timestamp is set
        if not message.timestamp:
            message.timestamp = datetime.datetime.now().isoformat()
            
        # Get current history
        history = self.get_history(session_id)
        if history is None:
            history = []
            
        # Add message to history
        message_dict = message.dict()
        history.append(message_dict)
        
        # Store updated history
        try:
            if self.redis_available:
                history_json = json.dumps(history)
                self.redis.set(self._get_key(session_id), history_json)
                self.redis.expire(self._get_key(session_id), self.ttl)
                logger.debug(f"Added message to Redis for session {session_id}")
            else:
                self.fallback_storage[session_id] = history
                logger.debug(f"Added message to memory for session {session_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            # If Redis fails, fall back to in-memory
            if not hasattr(self, 'fallback_storage'):
                self.fallback_storage = {}
            self.fallback_storage[session_id] = history
            self.redis_available = False
            return True
        
    def get_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the chat history for a session"""
        if not self.session_exists(session_id):
            return None
            
        try:
            if self.redis_available:
                history_json = self.redis.get(self._get_key(session_id))
                if history_json:
                    history = json.loads(history_json)
                    logger.debug(f"Retrieved {len(history)} messages from Redis for session {session_id}")
                    return history
                return []
            else:
                history = self.fallback_storage.get(session_id, [])
                logger.debug(f"Retrieved {len(history)} messages from memory for session {session_id}")
                return history
                
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            # If Redis fails, fall back to in-memory if we have it
            self.redis_available = False
            if hasattr(self, 'fallback_storage') and session_id in self.fallback_storage:
                return self.fallback_storage.get(session_id, [])
            return []
            
    def clear_session(self, session_id: str) -> bool:
        """Clear the chat history for a session"""
        if not self.session_exists(session_id):
            return False
            
        try:
            if self.redis_available:
                self.redis.delete(self._get_key(session_id))
                logger.info(f"Cleared session in Redis: {session_id}")
            else:
                self.fallback_storage.pop(session_id, None)
                logger.info(f"Cleared session in memory: {session_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            # If Redis fails, fall back to in-memory
            self.redis_available = False
            if hasattr(self, 'fallback_storage'):
                self.fallback_storage.pop(session_id, None)
            return True
            
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs"""
        try:
            if self.redis_available:
                pattern = self._get_key('*')
                keys = self.redis.keys(pattern)
                session_ids = [key.replace('chat:history:', '') for key in keys]
                return session_ids
            else:
                return list(self.fallback_storage.keys())
                
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            self.redis_available = False
            if hasattr(self, 'fallback_storage'):
                return list(self.fallback_storage.keys())
            return []
