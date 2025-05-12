from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import logging
import asyncio
from datetime import datetime, timedelta

# Import Qdrant configuration (must be imported before other modules)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qdrant_config
from .rag_pipeline import RagPipeline
from .chat_history import ChatHistoryManager
from .models import ChatMessage, SessionInfo
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News RAG Chatbot API")

# Load environment variables for CORS settings
from dotenv import load_dotenv
load_dotenv()

# Get CORS settings from environment variables
cors_origins = os.environ.get("CORS_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in cors_origins.split(",")] if cors_origins != "*" else ["*"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline and chat history manager
rag_pipeline = RagPipeline()
chat_history_manager = ChatHistoryManager()

# Store active websocket connections
active_connections: Dict[str, WebSocket] = {}

# Background refresh flag
last_refresh_time = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting RAG Chatbot API")
    
    # Initialize the RAG pipeline
    try:
        await rag_pipeline.initialize()
        logger.info("RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing RAG pipeline: {e}")
        
    # Schedule periodic article refresh (in a production app, this would use a proper task scheduler)
    background_tasks = BackgroundTasks()
    background_tasks.add_task(refresh_articles_periodically)
    
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("Shutting down RAG Chatbot API")

async def refresh_articles_periodically():
    """Periodically refresh news articles in the background"""
    global last_refresh_time
    
    while True:
        try:
            # Check if it's time to refresh (every 4 hours)
            current_time = datetime.now()
            if last_refresh_time is None or (current_time - last_refresh_time) > timedelta(hours=4):
                logger.info("Starting scheduled article refresh")
                success = await rag_pipeline.refresh_articles()
                if success:
                    last_refresh_time = current_time
                    logger.info(f"Articles refreshed successfully at {last_refresh_time}")
                else:
                    logger.warning("Scheduled article refresh failed")
        except Exception as e:
            logger.error(f"Error in periodic article refresh: {e}")
            
        # Wait for 1 hour before checking again
        await asyncio.sleep(60 * 60)

@app.get("/")
async def root():
    """Root endpoint to check API status"""
    return {
        "status": "active", 
        "message": "News RAG Chatbot API is running",
        "initialized": rag_pipeline.is_initialized
    }

@app.post("/api/session")
async def create_session():
    """Create a new chat session"""
    # Generate a new session ID
    session_id = str(uuid.uuid4())
    
    # Try to create the session, with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        success = chat_history_manager.create_session(session_id)
        if success:
            logger.info(f"Created new session: {session_id}")
            return {"session_id": session_id}
        else:
            # If failed, generate a new session ID and try again
            logger.warning(f"Failed to create session on attempt {attempt + 1}, retrying...")
            session_id = str(uuid.uuid4())
    
    # If we get here, all attempts failed
    logger.error("Failed to create session after multiple attempts")
    raise HTTPException(status_code=500, detail="Failed to create chat session")

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a session"""
    # Check if session exists, if not create it
    if not chat_history_manager.session_exists(session_id):
        logger.info(f"Session {session_id} not found, creating it")
        chat_history_manager.create_session(session_id)
        return {"history": []}
    
    # Get history
    history = chat_history_manager.get_history(session_id)
    if history is None:
        # This should not happen since we just created the session if it didn't exist
        logger.warning(f"Failed to get history for session: {session_id}")
        raise HTTPException(status_code=500, detail="Failed to get session history")
    
    logger.info(f"Retrieved history for session {session_id} with {len(history)} messages")
    return {"history": history}

@app.delete("/api/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear chat history for a session"""
    success = chat_history_manager.clear_session(session_id)
    if not success:
        logger.warning(f"Attempted to clear non-existent session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info(f"Cleared history for session: {session_id}")
    return {"status": "success", "message": "Session cleared"}

@app.post("/api/refresh")
async def manual_refresh():
    """Manually trigger a refresh of news articles"""
    global last_refresh_time
    
    try:
        logger.info("Manual article refresh triggered")
        success = await rag_pipeline.refresh_articles()
        if success:
            last_refresh_time = datetime.now()
            return {"status": "success", "message": "Articles refreshed successfully"}
        else:
            return {"status": "error", "message": "Failed to refresh articles"}
    except Exception as e:
        logger.error(f"Error in manual article refresh: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    active_connections[session_id] = websocket
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        # Always ensure the session exists
        if not chat_history_manager.session_exists(session_id):
            success = chat_history_manager.create_session(session_id)
            if success:
                logger.info(f"Created new session during WebSocket connection: {session_id}")
            else:
                logger.warning(f"Failed to create session during WebSocket connection: {session_id}")
                # Send error message to client
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Failed to create chat session. Please refresh the page."
                }))
                return
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message_text = message_data.get("message", "")
            
            logger.info(f"Received message in session {session_id}: {user_message_text[:30]}{'...' if len(user_message_text) > 30 else ''}")
            
            # Store user message in history
            user_message = ChatMessage(
                role="user",
                content=user_message_text,
                timestamp=message_data.get("timestamp")
            )
            chat_history_manager.add_message(session_id, user_message)
            
            # Process with RAG pipeline
            history = chat_history_manager.get_history(session_id)
            
            # Send processing message
            await websocket.send_text(json.dumps({
                "type": "status",
                "content": "processing"
            }))
            
            # Generate and stream the response
            full_response = ""
            try:
                async for token in rag_pipeline.generate_response(user_message_text, history):
                    full_response += token
                    await websocket.send_text(json.dumps({
                        "type": "stream",
                        "content": token
                    }))
                    
                logger.info(f"Generated response in session {session_id}: {full_response[:30]}{'...' if len(full_response) > 30 else ''}")
                    
            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                logger.error(error_message)
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": error_message
                }))
                full_response = error_message
            
            # Store bot response in history
            bot_message = ChatMessage(
                role="assistant",
                content=full_response,
                timestamp=None  # Will be set by the manager
            )
            chat_history_manager.add_message(session_id, bot_message)
            
            # Send end of stream marker
            await websocket.send_text(json.dumps({
                "type": "end",
                "content": ""
            }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"Error in websocket for session {session_id}: {str(e)}")
        if session_id in active_connections:
            del active_connections[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
