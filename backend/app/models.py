from pydantic import BaseModel
from typing import List, Optional
import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()

class SessionInfo(BaseModel):
    session_id: str
    created_at: str = datetime.datetime.now().isoformat()
    history: List[ChatMessage] = []

class NewsArticle(BaseModel):
    title: str
    content: str
    url: str
    published_date: Optional[str] = None
    source: str = "FirstPost"

class EmbeddedChunk(BaseModel):
    text: str
    embedding: List[float]
    article_id: str
    article_title: str
